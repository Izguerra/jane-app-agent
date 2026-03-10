import asyncio
import os
import logging
from livekit import api, rtc
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reproduce-issue")

async def main():
    logger.info("Starting reproduction script...")
    
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    if not api_key or not api_secret or not livekit_url:
        logger.error("Missing LiveKit env vars")
        return

    import uuid
    room_name = f"debug-room-{str(uuid.uuid4())[:8]}"
    participant_identity = f"debug-user-{str(uuid.uuid4())[:8]}"
    
    # Configure agent dispatch
    room_config = api.RoomConfiguration(
        agents=[
            api.RoomAgentDispatch(agent_name="supaagent-voice-agent")
        ]
    )

    # Generate token
    token = (api.AccessToken(api_key, api_secret)
             .with_grants(api.VideoGrants(room_join=True, room=room_name))
             .with_identity(participant_identity)
             .with_name("Debug User")
             .with_room_config(room_config)
             .to_jwt())
             
    logger.info(f"Generated token for room {room_name}")
    
    # Connect to room
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"Participant connected: {participant.identity}")
        
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
        
    @room.on("disconnected")
    def on_disconnected(reason):
        logger.info(f"Disconnected: {reason}")

    try:
        logger.info(f"Connecting to {livekit_url}...")
        await room.connect(livekit_url, token)
        logger.info("Connected to room")
        
        # Publish audio track to simulate user speaking
        # (Optional, but might trigger VAD)
        
        logger.info("Waiting for agent...")
        await asyncio.sleep(30) # Wait for 30 seconds
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await room.disconnect()
        logger.info("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
