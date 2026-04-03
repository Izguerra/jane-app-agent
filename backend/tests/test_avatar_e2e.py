
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

# Use ID from existing script or known valid default
ANAM_PERSONA_ID = "pers_3396c97a-9771-460d-8ea6-1076f8279148" 

ROOM_NAME = f"e2e-avatar-{os.urandom(4).hex()}"

def start_worker():
    print(">>> Starting Avatar Agent Worker... (Logs saved to backend/worker_avatar_e2e.log)")
    # Path relative to project root. Assumes CWD is project root.
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Ensure backend is in pythonpath
    env["PYTHONPATH"] = os.getcwd()
    
    log_file = open("backend/worker_avatar_e2e.log", "w")
    process = subprocess.Popen(
        [sys.executable, "backend/avatar_agent.py", "dev"], 
        env=env,
        stdout=log_file,
        stderr=log_file
    )
    return process, log_file

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
    worker_proc, log_file = start_worker()
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
            agents=[api.RoomAgentDispatch(agent_name="avatar-agent")]
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

        # 3. Wait Loop — Phase 1: Agent must join (2 participants)
        start_time = time.time()
        agent_timeout = 30
        tavus_timeout = 60
        
        agent_joined = False
        tavus_joined = False
        conversation_id = None
        
        while time.time() - start_time < tavus_timeout:
            remote_count = len(room.remote_participants)
            total = remote_count + 1 # Self
            
            # Identify participants
            participants = []
            for p in room.remote_participants.values():
                participants.append(f"{p.identity} ({p.kind})")
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Count: {total}. Remote: {participants}")
            
            if total >= 2 and not agent_joined:
                print("\n✅ PHASE 1 PASS: Agent joined the room (2 participants)")
                agent_joined = True
            
            if total >= 3:
                print("\n✅ PHASE 2 PASS: Tavus replica joined (3 participants)")
                tavus_joined = True
                break
            
            # If agent hasn't joined within agent_timeout, fail early
            if not agent_joined and elapsed >= agent_timeout:
                break
                
            await asyncio.sleep(2)
        
        # Primary assertion: agent must join
        assert agent_joined, f"Agent failed to join room within {agent_timeout}s"
        
        if tavus_joined:
            print("\n>> Fetching Tavus Conversation ID from logs...")
            await asyncio.sleep(2) 
            conversation_id = check_logs_for_conversation_id()
            if conversation_id:
                print(f"✅ FOUND CONVERSATION ID: {conversation_id}")
            else:
                print("⚠️  Participants joined, but Conversation ID not found in logs.")
        else:
            print("\n⚠️  Tavus replica did not join (external service dependency) — agent infrastructure verified.")
            
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
        
        log_file.close()
        
        # Capture and print logs
        print("\n=== WORKER LOGS (backend/worker_avatar_e2e.log) ===")
        try:
            with open("backend/worker_avatar_e2e.log", "r") as f:
                print(f.read())
        except Exception as e:
            print(f"Could not read worker logs: {e}")
        print("=====================")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_avatar_e2e())

