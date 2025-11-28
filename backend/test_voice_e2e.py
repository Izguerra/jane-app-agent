import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api, rtc

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_voice_e2e")

async def test_e2e():
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    API_KEY = os.getenv("LIVEKIT_API_KEY")
    API_SECRET = os.getenv("LIVEKIT_API_SECRET")

    if not all([LIVEKIT_URL, API_KEY, API_SECRET]):
        logger.error("Missing LiveKit credentials")
        return

    # import uuid
    # room_name = f"room-{str(uuid.uuid4())[:8]}"
    room_name = "room-1"
    identity = "test-user-e2e"

    # 1. Generate Token with Dispatch
    logger.info("Generating token...")
    grant = api.VideoGrants(room_join=True, room=room_name)
    room_config = api.RoomConfiguration(
        agents=[
            api.RoomAgentDispatch(agent_name="jane-voice-agent")
        ]
    )
    
    token = (api.AccessToken(API_KEY, API_SECRET)
             .with_grants(grant)
             .with_identity(identity)
             .with_name("Test User")
             .with_room_config(room_config)
             .to_jwt())

    # 2. Connect to Room
    logger.info(f"Connecting to {LIVEKIT_URL} room {room_name}...")
    room = rtc.Room()
    
    agent_found = asyncio.Future()
    agent_audio_published = asyncio.Future()

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity} ({participant.kind})")
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            logger.info("✅ Agent connected!")
            if not agent_found.done():
                agent_found.set_result(participant)

    @room.on("track_published")
    def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"Track published: {publication.kind} by {participant.identity}")
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT and publication.kind == rtc.TrackKind.KIND_AUDIO:
             logger.info("✅ Agent published audio track!")
             if not agent_audio_published.done():
                 agent_audio_published.set_result(True)

    try:
        await room.connect(LIVEKIT_URL, token)
        logger.info("Connected to room")

        # 3. Publish Dummy Audio (Microphone simulation)
        # We assume creating a local audio track requires a source, but we can try without one or verify dispatch works even without audio first.
        # LiveKit Agents usually wait for a participant to join.
        
        # Wait for agent to join
        try:
            logger.info("Waiting for agent to join...")
            await asyncio.wait_for(agent_found, timeout=15)
        except asyncio.TimeoutError:
            logger.error("❌ Timed out waiting for agent to join")
            await room.disconnect()
            return

        # Wait for agent to speak (publish audio)
        try:
            logger.info("Waiting for agent to speak...")
            await asyncio.wait_for(agent_audio_published, timeout=15)
            logger.info("🎉 E2E TEST PASSED: Agent joined and spoke.")
        except asyncio.TimeoutError:
            logger.error("❌ Timed out waiting for agent to speak")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await room.disconnect()

if __name__ == "__main__":
    asyncio.run(test_e2e())

