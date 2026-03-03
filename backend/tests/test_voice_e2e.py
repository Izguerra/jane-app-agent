
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

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

ROOM_NAME = f"e2e-voice-{os.urandom(4).hex()}"

def start_worker():
    print(f">>> Starting Voice Agent Worker... (Logging to backend/worker_voice_e2e.log)")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.getcwd()
    
    log_file = open("backend/worker_voice_e2e.log", "w")
    process = subprocess.Popen(
        [sys.executable, "backend/voice_agent.py", "dev"], 
        env=env,
        stdout=log_file,
        stderr=log_file
    )
    return process, log_file

@pytest.mark.asyncio
async def test_voice_e2e():
    print(f"\n=== E2E Voice Verification Test ===")
    print(f"Room: {ROOM_NAME}")
    
    worker_proc, log_file = start_worker()
    time.sleep(5)
    
    try:
        metadata = {
            "mode": "voice",
            "voiceId": "alloy",
            "workspace_id": "wrk_e2e_voice"
        }

        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name="supaagent-voice-agent")]
        )

        grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
        grant.can_publish = True
        grant.can_subscribe = True

        token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                 .with_grants(grant)
                 .with_identity(f"user-voice-e2e-{os.urandom(2).hex()}")
                 .with_name("Voice E2E Tester")
                 .with_metadata(json.dumps(metadata))
                 .with_room_config(room_config)
                 .to_jwt())

        print(">> Connecting User...")
        room = rtc.Room()
        await room.connect(LIVEKIT_URL, token)
        
        start_time = time.time()
        timeout = 45 
        success = False
        
        while time.time() - start_time < timeout:
            total = len(room.remote_participants) + 1
            print(f"[{int(time.time() - start_time)}s] Participants: {total}")
            
            if total >= 2:
                print("✅ SUCCESS: 2 Participants Joined!")
                success = True
                break
            await asyncio.sleep(2)
            
        assert success, "Timed out waiting for agent to join room"
        await room.disconnect()
        
    finally:
        print(">> Killing worker process...")
        if worker_proc.poll() is None:
             worker_proc.terminate()
             try:
                 worker_proc.wait(timeout=5)
             except:
                 worker_proc.kill()
        
        log_file.close()
        
        print("\n=== WORKER LOGS (backend/worker_voice_e2e.log) ===")
        with open("backend/worker_voice_e2e.log", "r") as f:
            print(f.read())
        print("=====================")

if __name__ == "__main__":
    asyncio.run(test_voice_e2e())
