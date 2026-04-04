import asyncio
import os
import json
import logging
import time
from livekit import api, rtc
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Use the IDs discovered from the database
WORKSPACE_ID = "wrk_000VAHZIJvJ9oiRT0OczrnjMug"
AGENT_ID = "set_000VAHZISYj7YfNVeMy2f4JxNP"
ROOM_NAME = f"{WORKSPACE_ID}_dashboard_agent_{AGENT_ID}_{os.urandom(2).hex()}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-e2e")

async def test_gemini_greeting():
    print(f"\n=== Gemini 3.1 Stabilization Verification ===")
    print(f"Room: {ROOM_NAME}")
    print(f"Workspace: {WORKSPACE_ID}")

    metadata = {
        "mode": "voice",
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID
    }

    # Dispatch configuration
    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name="voice-agent")]
    )

    grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
    grant.can_publish = True
    grant.can_subscribe = True

    token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
             .with_grants(grant)
             .with_identity(f"tester-{os.urandom(2).hex()}")
             .with_name("Gemini Tester")
             .with_metadata(json.dumps(metadata))
             .with_room_config(room_config)
             .to_jwt())

    room = rtc.Room()
    
    greeting_received = asyncio.Event()
    received_text = ""

    @room.on("transcription_received")
    def on_transcription(transcription: rtc.Transcription):
        nonlocal received_text
        # We only care about the agent's transcript
        if transcription.participant.identity.startswith("agent-") or "voice-agent" in transcription.participant.identity:
            text = " ".join([segment.text for segment in transcription.segments])
            logger.info(f"🎤 Agent Transcribed: {text}")
            received_text = text
            greeting_received.set()

    @room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"👤 Participant joined: {participant.identity}")

    try:
        logger.info("Connecting to room...")
        await room.connect(LIVEKIT_URL, token)
        logger.info("Connected. Waiting for agent and greeting...")

        # Wait for greeting with 45s timeout
        try:
            await asyncio.wait_for(greeting_received.wait(), timeout=45.0)
            print(f"\n✅ SUCCESS: Welcome greeting received!")
            print(f"Transcript: \"{received_text}\"")
        except asyncio.TimeoutError:
            print("\n❌ FAILURE: Timed out waiting for greeting.")
            # Check if agent even joined
            agents = [p for p in room.remote_participants.values() if "voice-agent" in p.identity]
            if not agents:
                print("Hint: The voice-agent never joined the room. Check voice_agent.log.")
            else:
                print("Hint: The agent joined but remained silent. Check Handshake Guard logs.")

    finally:
        await room.disconnect()
        print("=== Test Complete ===\n")

if __name__ == "__main__":
    asyncio.run(test_gemini_greeting())
