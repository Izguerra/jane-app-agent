import asyncio
import os
import json
import logging
from dotenv import load_dotenv
from livekit import api, rtc

load_dotenv()

# Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

REPLICA_ID = "r1a4e22fa0d9"
PERSONA_ID = "p11bf212e353"
ROOM_NAME = "test-avatar-e2e-v2"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e-test")

async def main():
    logger.info("--- Starting E2E Avatar Agent Test ---")

    # 1. Generate Token with proper Metadata
    room_meta = {
        "mode": "avatar",
        "tavusReplicaId": REPLICA_ID,
        "tavusPersonaId": PERSONA_ID,
        "workspace_id": "debug_test",
        "voice_id": "Josh"
    }

    # 1.5 Setup Dispatch via Room Config (Standard Auto-Dispatch)
    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name="supaagent-avatar-agent")]
    )

    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity("test_user_inspector") \
        .with_name("Inspector Gadget") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=ROOM_NAME,
        )) \
        .with_room_config(room_config) \
        .to_jwt()

    # Create room with metadata if needed
    lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    logger.info(f"Creating room {ROOM_NAME} with metadata...")
    try:
        await lkapi.room.create_room(api.CreateRoomRequest(
            name=ROOM_NAME,
            metadata=json.dumps(room_meta),
            empty_timeout=60,
        ))
        logger.info("Room created successfully.")
    except Exception as e:
        logger.warning(f"Room creation warning (might exist): {e}")

    # 2. Connect to Room
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"PARTICIPANT CONNECTED: {participant.identity}")
    
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        logger.info(f"TRACK SUBSCRIBED: {track.kind} from {participant.identity}")
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info("✅ SUCCESS: Video Track Received! Tavus Connected!")

    logger.info(f"Connecting to {LIVEKIT_URL}...")
    try:
        await room.connect(LIVEKIT_URL, token)
        logger.info("Connected to Room.")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return

    # 3. Wait for Agent
    logger.info("Waiting for Agent to join...")
    
    # Wait loop
    for i in range(30):
        await asyncio.sleep(1)
        # Check remote participants
        for p_id, p in room.remote_participants.items():
            if "supaagent" in p.identity:
                # logger.info(f"Found Agent: {p.identity}")
                pass
            
    logger.info("Test finished. Disconnecting.")
    await room.disconnect()
    await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
