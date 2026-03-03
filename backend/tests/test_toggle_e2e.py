
import asyncio
import os
import json
import logging
import time
import subprocess
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

# Load env
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# IDs
TAVUS_REPLICA_ID = "r79e1c033f" # Default fro test
TAVUS_PERSONA_ID = "p7fb0be3"

async def run_test():
    print("=== STARTING TOGGLE E2E TEST ===")
    
    # 1. Start Workers (assuming they might not be running or we want isolation)
    # Actually, we rely on the User's running ecosystem or start our own.
    # To be safe and isolated, let's start a dedicated worker process for this test.
    # We need BOTH voice and avatar functionality. Backend/avatar_agent.py handles both?
    # Usually they are separate or combined.
    # Let's assume we run 'backend/avatar_agent.py dev' which (based on code) handles logic.
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env["PYTHONUNBUFFERED"] = "1"
    
    # Unique names for isolation
    voice_agent_name = "supaagent-voice-test"
    avatar_agent_name = "supaagent-avatar-test"
    
    env_avatar = env.copy()
    env_avatar["AGENT_NAME"] = avatar_agent_name
    
    print(">> Starting Avatar Agent Worker...")
    import sys
    worker_avatar = subprocess.Popen(
        [sys.executable, "backend/avatar_agent.py", "dev"],
        env=env_avatar,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    env_voice = env.copy()
    env_voice["AGENT_NAME"] = voice_agent_name
    
    print(f">> Starting Voice Agent Worker ({voice_agent_name})...")
    worker_voice = subprocess.Popen(
        [sys.executable, "backend/voice_agent.py", "dev"],
        env=env_voice,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10) # Warmup both

    try:
        lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        
        # --- TEST 1: VOICE MODE ---
        print("\n[TEST 1] Connecting Voice Agent...")
        room_voice = f"toggle-test-voice-{os.urandom(2).hex()}"
        
        grand_voice = api.VideoGrants(room_join=True, room=room_voice)
        room_config_voice = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name=voice_agent_name)]
        )
        
        token_voice = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_grants(grand_voice)
            .with_identity("user-tester")
            .with_room_config(room_config_voice)
            .to_jwt())

        # Connect Client
        room_client = rtc.Room()
        await room_client.connect(LIVEKIT_URL, token_voice)
        print(f"User connected to {room_voice} | SID: {await room_client.sid}")
        for _ in range(10):
            if len(room_client.remote_participants) >= 1:
                break
            await asyncio.sleep(1)
            
        parts_voice = len(room_client.remote_participants) + 1
        print(f"Participants Count: {parts_voice}")
        for p in room_client.remote_participants.values():
            print(f" - Remote Participant: Identity={p.identity}, Name={p.name}")
        
        if parts_voice != 2:
            print(f"FAIL: Expected 2 participants, got {parts_voice}")
        else:
            print("PASS: Voice Connection Established")
            
        await room_client.disconnect()

        # --- TEST 2: AVATAR MODE ---
        print("\n[TEST 2] Connecting Avatar Agent...")
        room_avatar = f"toggle-test-avatar-{os.urandom(2).hex()}"
        
        grant_avatar = api.VideoGrants(room_join=True, room=room_avatar)
        grant_avatar.can_publish = True 
        
        meta = {
            "mode": "avatar", 
            "tavus_replica_id": TAVUS_REPLICA_ID,
            "tavus_persona_id": TAVUS_PERSONA_ID,
            "voice_id": "alloy"
        }
        
        room_config_avatar = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name=avatar_agent_name)],
            metadata=json.dumps(meta) 
        )
        
        token_avatar = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_grants(grant_avatar)
            .with_identity("user-tester")
            .with_room_config(room_config_avatar)
            .with_metadata(json.dumps(meta))
            .to_jwt())
            
        room_avatar_client = rtc.Room()
        await room_avatar_client.connect(LIVEKIT_URL, token_avatar)
        print(f"User connected to {room_avatar} | SID: {await room_avatar_client.sid}")
        
        # Wait for both Agent and Tavus
        for _ in range(25):
            if len(room_avatar_client.remote_participants) >= 2:
                break
            await asyncio.sleep(1)
            
        parts_1 = len(room_avatar_client.remote_participants) + 1
        print(f"Participants Count: {parts_1}")
        for p in room_avatar_client.remote_participants.values():
            print(f" - Remote Participant: Identity={p.identity}, Name={p.name}")
        
        # Check for Tavus Conversation ID in room metadata
        tavus_id = None
        for _ in range(20):
            if room_avatar_client.metadata:
                try:
                    rm_meta = json.loads(room_avatar_client.metadata)
                    if rm_meta.get("tavus_conversation_id"):
                        tavus_id = rm_meta['tavus_conversation_id']
                        print(f"Tavus Conversation ID: {tavus_id}")
                        break
                except: pass
            await asyncio.sleep(1)

        if parts_1 != 3:
            print(f"FAIL: Expected 3 participants, got {parts_1}")
        else:
            print("PASS: Avatar Connection Established with 3 participants")
            
        await room_avatar_client.disconnect()

        # --- TEST 3: BACK TO VOICE ---
        print("\n[TEST 3] Switching Back to Voice...")
        room_voice_2 = f"toggle-test-voice-2-{os.urandom(2).hex()}"
        
        grant_voice_2 = api.VideoGrants(room_join=True, room=room_voice_2)
        room_config_voice_2 = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name=voice_agent_name)]
        )
         
        token_voice_2 = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_grants(grant_voice_2)
            .with_identity("user-tester")
            .with_room_config(room_config_voice_2)
            .to_jwt())
            
        room_voice_client_2 = rtc.Room()
        await room_voice_client_2.connect(LIVEKIT_URL, token_voice_2)
        print(f"User connected to {room_voice_2} | SID: {await room_voice_client_2.sid}")
        
        for _ in range(10):
            if len(room_voice_client_2.remote_participants) >= 1:
                break
            await asyncio.sleep(1)
            
        parts_2 = len(room_voice_client_2.remote_participants) + 1
        print(f"Participants: {parts_2}")
        
        if parts_2 != 2:
            print(f"FAIL: Expected 2 participants, got {parts_2}")
            for p in room_voice_client_2.remote_participants.values():
                print(f" - Identity: {p.identity}, Name: {p.name}")
        else:
            print("PASS: Voice Connection Restored")
            
        await room_voice_client_2.disconnect()
        await lkapi.aclose()
        
    finally:
        print("Killing workers...")
        if 'worker_avatar' in locals():
            worker_avatar.terminate()
            worker_avatar.wait()
        if 'worker_voice' in locals():
            worker_voice.terminate()
            worker_voice.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
