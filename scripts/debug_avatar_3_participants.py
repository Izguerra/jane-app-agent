import asyncio
import os
import json
import logging
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Tavus Details from User Context
TAVUS_PERSONA_ID = "p7fb0be3" 
TAVUS_REPLICA_ID = "r79e1c033f" 

ROOM_NAME = f"avatar-check-{os.urandom(4).hex()}"

async def main():
    print(f"--- 3-Participant Verification Test ---")
    print(f"Target Room: {ROOM_NAME}")

    # 1. Token with Agent Dispatch + Avatar Metadata
    print("1. Generating Token...")
    
    metadata = {
        "mode": "avatar",
        "tavusReplicaId": TAVUS_REPLICA_ID,
        "tavusPersonaId": TAVUS_PERSONA_ID,
        "voiceId": "alloy",
        "instructions": "You are a test avatar.",
        "workspace_id": "wrk_debug_script"
    }

    grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
    grant.can_publish = True
    grant.can_subscribe = True

    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name="supaagent-voice-agent")]
    )

    token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
             .with_grants(grant)
             .with_identity("verify-user-1")
             .with_name("Verification User")
             .with_metadata(json.dumps(metadata))
             .with_room_config(room_config)
             .to_jwt())

    # 2. Connect
    print("2. Connecting...")
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant):
        print(f"Event: Participant Joined: {participant.identity} ({participant.kind})")

    try:
        await room.connect(LIVEKIT_URL, token)
        print(">> Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    # 3. Monitor for 3 Participants (Self + Agent + Tavus)
    print("3. Waiting for full session (User + Agent + Tavus)...")
    
    tavus_joined = False
    agent_joined = False
    
    # Wait loop
    for i in range(40): # 40s timeout
        remote_count = len(room.remote_participants)
        total_count = remote_count + 1 # + Self
        
        # Check specific identities if possible
        for p in room.remote_participants.values():
            if p.kind == "agent": agent_joined = True
            # Tavus usually joins as a SIP participant or with a specific identity prefix depending on integration
            # We assume any non-agent remote participant *might* be Tavus if using SIP, 
            # Or Tavus plugin might register as a hidden participant? 
            # Usually Tavus is a standard participant sending video.
            if "tavus" in p.identity.lower() or "sip" in p.identity.lower() or p.kind == "standard": 
                tavus_joined = True # Heuristic
        
        print(f"   [Time {i}s] Total Grid: {total_count} (You + {remote_count} Remote)")
        
        if total_count >= 3:
            print("\nSUCCESS: 3 Participants Detected!")
            for p in room.remote_participants.values():
                print(f"   - Remote: {p.identity} ({p.kind})")
            break
            
        await asyncio.sleep(1)

    if total_count < 3:
        print("\nFAILURE: Did not reach 3 participants.")
        for p in room.remote_participants.values():
             print(f"   - Found: {p.identity} ({p.kind})")

    await room.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
