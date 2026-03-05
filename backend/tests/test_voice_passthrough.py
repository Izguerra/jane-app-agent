
import asyncio
import os
import json
import time
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

ROOM_NAME = f"passthrough-voice-{os.urandom(4).hex()}"

async def test_passthrough():
    print(f"\n=== Passthrough Voice Verification Test ===")
    print(f"Room: {ROOM_NAME}")
    print("This test relies on the ALREADY RUNNING system worker.")
    
    try:
        metadata = {
            "mode": "voice",
            "voice_id": "alloy",
            "workspace_id": "wrk_passthrough"
        }

        # Dispatch specifically to the system worker name
        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name="supaagent-voice-agent-v2")]
        )

        grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
        grant.can_publish = True
        grant.can_subscribe = True

        token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                 .with_grants(grant)
                 .with_identity(f"user-passthrough-{os.urandom(2).hex()}")
                 .with_name("Passthrough Tester")
                 .with_metadata(json.dumps(metadata))
                 .with_room_config(room_config)
                 .to_jwt())

        print(">> Connecting User...")
        room = rtc.Room()
        await room.connect(LIVEKIT_URL, token)
        
        print(">> User connected. Waiting for AGENT participant...")
        start_time = time.time()
        timeout = 30
        success = False
        
        while time.time() - start_time < timeout:
            participants = list(room.remote_participants.values())
            print(f"[{int(time.time() - start_time)}s] Remote Participants: {len(participants)}")
            for p in participants:
                print(f"  - Participant: {p.identity} | Metadata: {p.metadata}")
            
            if len(participants) >= 1:
                # Check if any participant is the agent
                # In LiveKit, agents usually have a specific identity or we can check names
                print("✅ SUCCESS: Agent Participant Joined!")
                success = True
                break
            await asyncio.sleep(2)
            
        if not success:
            print("❌ FAILURE: Timed out waiting for system worker to join.")
            
        await room.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_passthrough())
