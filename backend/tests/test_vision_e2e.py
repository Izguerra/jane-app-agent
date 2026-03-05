
import asyncio
import os
import json
import logging
import subprocess
import time
import numpy as np
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

# Load env from project root
load_dotenv() 

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Use ID from existing script or known valid default
TAVUS_PERSONA_ID = "p7fb0be3" 
TAVUS_REPLICA_ID = "r79e1c033f" 

ROOM_NAME = f"e2e-vision-{os.urandom(4).hex()}"

def start_worker():
    print(">>> Starting Avatar Agent Worker...")
    # Path relative to project root. Assumes CWD is project root.
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.getcwd()
    
    process = subprocess.Popen(
        ["python", "backend/avatar_agent.py", "dev"], 
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def check_logs_for_vision_success():
    log_path = "backend/debug_avatar.log"
    if not os.path.exists(log_path):
        return False
    
    with open(log_path, "r") as f:
        content = f.read()
        if "Vision Check: Injected video frame into LLM context" in content:
            return True
    return False

async def main():
    print(f"=== E2E Vision Verification Test ===")
    print(f"Room: {ROOM_NAME}")
    
    # Start Worker
    worker_proc = start_worker()
    time.sleep(3) # Warmup
    
    try:
        # 1. Generate User Token
        metadata = {
            "mode": "avatar",
            "tavusReplicaId": TAVUS_REPLICA_ID,
            "tavusPersonaId": TAVUS_PERSONA_ID,
            "voiceId": "alloy",
            "instructions": "You are a test avatar.",
            "workspace_id": "wrk_e2e_vision"
        }

        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name="supaagent-voice-agent")]
        )

        grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
        grant.can_publish = True
        grant.can_subscribe = True

        token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                 .with_grants(grant)
                 .with_identity(f"user-vision-{os.urandom(2).hex()}")
                 .with_name("Vision Tester")
                 .with_metadata(json.dumps(metadata))
                 .with_room_config(room_config)
                 .to_jwt())

        # 2. Connect User
        print(">> Connecting User to LiveKit...")
        room = rtc.Room()
        
        @room.on("participant_connected")
        def on_participant(p):
            print(f"[Event] joined: {p.identity} ({p.kind})")

        await room.connect(LIVEKIT_URL, token)
        print(">> Connected. Publishing Video...")

        # 3. Publish Video Track (Color Frame)
        # Create a red frame
        width, height = 640, 480
        # Red: Y=76, U=84, V=255 (approx) in I420? Or just use ARGB.
        # LiveKit VideoFrame accepts argb using `from_argb`?
        # Actually simplest is just random noise or check API.
        
        # We need a source
        source = rtc.VideoSource(width, height)
        track = rtc.LocalVideoTrack.create_video_track("test_camera", source)
        options = rtc.TrackPublishOptions()
        options.source = rtc.TrackSource.SOURCE_CAMERA
        
        publication = await room.local_participant.publish_track(track, options)
        print(f">> Published Video Track: {publication.sid}")

        # Start loop to feed frames
        async def feed_frames():
            print(">> Starting frame feed...")
            try:
                while True:
                    # Create a simple blue frame (ARGB)
                    # 4 bytes per pixel: B, G, R, A (Little Endian?)
                    # Let's use gray
                    data = np.full((height, width, 4), 128, dtype=np.uint8) 
                    # Set Alpha to 255
                    data[:, :, 3] = 255
                    
                    frame = rtc.VideoFrame(width, height, rtc.VideoBufferType.RGBA, data.tobytes())
                    source.capture_frame(frame)
                    await asyncio.sleep(0.033) # 30fps
            except asyncio.CancelledError:
                pass

        feed_task = asyncio.create_task(feed_frames())

        # 4. Wait for Verification
        print(">> Waiting for Agent to acknowledge vision...")
        start_time = time.time()
        timeout = 45
        success = False
        
        while time.time() - start_time < timeout:
            if check_logs_for_vision_success():
                print("\n✅ SUCCESS: Vision Check Log Found! Agent is seeing video.")
                success = True
                break
            
            print(f"Waiting... ({int(time.time() - start_time)}s)")
            await asyncio.sleep(2)
            
        if not success:
            print("\n❌ FAILURE: Vision Check Log NOT found after timeout.")
            
        feed_task.cancel()
        await room.disconnect()
        
    finally:
        print(">> Killing worker process...")
        if worker_proc.poll() is None:
             worker_proc.terminate()
             try:
                 worker_proc.wait(timeout=5)
             except:
                 worker_proc.kill()
        
        # Print logs
        stdout_data, stderr_data = worker_proc.communicate()
        print("\n=== WORKER STDOUT ===")
        print(stdout_data.decode("utf-8", errors="replace") if stdout_data else "<Empty>")
        
        if success:
            print("\n✅ TEST PASSED")
            exit(0)
        else:
            print("\n❌ TEST FAILED")
            exit(1)

if __name__ == "__main__":
    asyncio.run(main())
