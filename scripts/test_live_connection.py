import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api, rtc

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_connection")

async def test_connection():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    room_name = "test-agent-connection-final"
    
    lkapi = api.LiveKitAPI(url, api_key, api_secret)
    room_opts = api.CreateRoomRequest(
        name=room_name,
        agents=[api.RoomAgentDispatch(agent_name="supaagent-voice-v2.1")],
    )
    
    try:
        await lkapi.room.create_room(room_opts)
        logger.info(f"Created room: {room_name}")
    except Exception as e:
        logger.error(f"Failed to create room: {e}")
        await lkapi.aclose()
        return

    token = (api.AccessToken(api_key, api_secret)
             .with_identity("test-user-final")
             .with_grants(api.VideoGrants(room_join=True, room=room_name))
             .to_jwt())

    room = rtc.Room()
    agent_joined = asyncio.Event()

    @room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"Participant: {participant.identity} joined")
        if "agent" in participant.identity or participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            agent_joined.set()

    await room.connect(url, token)
    try:
        await asyncio.wait_for(agent_joined.wait(), timeout=15)
        logger.info("TEST PASSED: Agent successfully joined.")
    except asyncio.TimeoutError:
        logger.error("TEST FAILED: Agent did not join.")
    finally:
        await room.disconnect()
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(test_connection())
