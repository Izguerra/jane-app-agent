
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

ROOM_NAME = f"passthrough-avatar-{os.urandom(4).hex()}"

async def test_passthrough():
    print(f"\n=== Passthrough Avatar Verification Test ===")
    print(f"Room: {ROOM_NAME}")
    
    try:
        metadata = {
            "mode": "avatar",
            "workspace_id": "wrk_passthrough_avatar",
            "tavus_replica_id": "r79796030c",
            "tavus_persona_id": "p683b5849"
        }

        # Dispatch specifically to the system avatar worker name
        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name="supaagent-avatar-agent-v2")]
        )

        grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
        grant.can_publish = True
        grant.can_subscribe = True

        token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                 .with_grants(grant)
                 .with_identity(f"user-avatar-pass-{os.urandom(2).hex()}")
                 .with_name("Avatar Passthrough")
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
                print(f"  - Participant: {p.identity} | Name: {p.name}")
            
            if len(participants) >= 1:
                print("✅ SUCCESS: Agent Participant Joined!")
                success = True
                break
            await asyncio.sleep(2)
            
        if not success:
            print("❌ FAILURE: Timed out waiting for avatar system worker.")
            
        await room.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_passthrough())
