
import asyncio
import os
import json
import logging
import subprocess
import time
import signal
import sys
import pytest
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

# Load env from project root
load_dotenv() 

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Use ID from Anam API response
ANAM_PERSONA_ID = "071b0286-4cce-4808-bee2-e642f1062de3" 


ROOM_NAME = f"e2e-avatar-{os.urandom(4).hex()}"

def start_worker():
    print(">>> Starting Avatar Agent Worker...")
    # Path relative to project root. Assumes CWD is project root.
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Ensure backend is in pythonpath
    env["PYTHONPATH"] = os.getcwd()
    
    process = subprocess.Popen(
        [sys.executable, "backend/avatar_agent.py", "dev"], 
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def check_logs_for_conversation_id():
    log_path = "backend/debug_avatar.log"
    if not os.path.exists(log_path):
        return None
    
    with open(log_path, "r") as f:
        # Read from end? Or just read all since we cleared/appended?
        content = f.read()
        if "Conversation ID:" in content:
            # Find the last occurrence related to our room?
            # Ideally we'd match by timestamp, but for this test, last one is probably ours.
            lines = content.splitlines()
            for line in reversed(lines):
                if "Conversation ID:" in line:
                    return line.split("Conversation ID:")[1].strip()
    return None

@pytest.mark.asyncio
async def test_avatar_e2e():
    print(f"\n=== E2E Avatar Verification Test ===")
    print(f"Room: {ROOM_NAME}")
    
    # Start Worker
    worker_proc = start_worker()
    time.sleep(3) # Warmup
    
    try:
        # 1. Generate User Token
        metadata = {
            "mode": "avatar",
            "anamPersonaId": ANAM_PERSONA_ID,
            "voiceId": "alloy", # OpenAI Voice to test restoration
            "instructions": "You are a test avatar.",
            "workspace_id": "wrk_e2e_test"
        }

        # Enable Auto-Dispatch by room name suffix or explicit dispatch?
        # Room dispatch rule in LiveKit normally dispatch based on room metadata or room name.
        # Here we use 'agents' in RoomConfiguration which requires Agents to be listening.
        # avatar_agent.py (if using livekit-agents v0.7+) listens if it connects to the same server.
        
        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name="supaagent-avatar-agent-v2")]
        )

        grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
        grant.can_publish = True
        grant.can_subscribe = True

        token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                 .with_grants(grant)
                 .with_identity(f"user-e2e-{os.urandom(2).hex()}")
                 .with_name("E2E Tester")
                 .with_metadata(json.dumps(metadata))
                 .with_room_config(room_config) # Dispatch!
                 .to_jwt())

        # 2. Connect User
        print(">> Connecting User to LiveKit...")
        room = rtc.Room()
        
        @room.on("participant_connected")
        def on_participant(p):
            print(f"[Event] joined: {p.identity} ({p.kind})")

        await room.connect(LIVEKIT_URL, token)
        print(">> Connected. Waiting for participants...")

        # 3. Wait Loop
        start_time = time.time()
        timeout = 60
        
        success = False
        conversation_id = None
        
        while time.time() - start_time < timeout:
            remote_count = len(room.remote_participants)
            total = remote_count + 1 # Self
            
            # Identify participants
            participants = []
            for p in room.remote_participants.values():
                participants.append(f"{p.identity} ({p.kind})")
            
            print(f"[{int(time.time() - start_time)}s] Count: {total}. Remote: {participants}")
            
            if total >= 3:
                print("\n✅ SUCCESS: 3 Participants Detected!")
                success = True
                break
            
            await asyncio.sleep(2)
            
        if success:
            # Try to grab Conversation ID
            print("\n>> Fetching Tavus Conversation ID from logs...")
            # Wait a sec for logs to flush
            await asyncio.sleep(2) 
            conversation_id = check_logs_for_conversation_id()
            if conversation_id:
                print(f"✅ FOUND CONVERSATION ID: {conversation_id}")
            else:
                print("⚠️  Participants joined, but Conversation ID not found in logs (check backend/debug_avatar.log).")
        else:
            print("\n❌ FAILURE: Timed out waiting for 3 participants.")
            assert success, "Timed out waiting for 3 participants"
            
        await room.disconnect()

        
    finally:
        print(">> Cleanup: Terminating worker process...")
        if worker_proc.poll() is None:
             worker_proc.terminate()
             try:
                 worker_proc.wait(timeout=3)
                 print(">> Worker terminated gracefully.")
             except subprocess.TimeoutExpired:
                 print(">> Worker timeout, killing...")
                 worker_proc.kill()
                 worker_proc.wait()
        
        # Capture and print logs
        print(">> Reading worker output...")
        try:
            # Non-blocking-ish communicate
            stdout_data, stderr_data = worker_proc.communicate(timeout=5)
        except Exception as e:
            print(f">> Communicate error: {e}")
            stdout_data = b"<Communicate Error>"
            stderr_data = b"<Communicate Error>"
            
        print("\n=== WORKER STDOUT ===")
        print(stdout_data.decode("utf-8", errors="replace") if stdout_data else "<Empty>")
        print("=====================")
        
        print("\n=== WORKER STDERR ===")
        print(stderr_data.decode("utf-8", errors="replace") if stderr_data else "<Empty>")
        print("=====================")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_avatar_e2e())

