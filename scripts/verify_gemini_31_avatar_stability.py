import asyncio
import os
import json
import logging
from livekit import api, rtc
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Test name to track in dashboard
ROOM_NAME = f"verify-avatar-{os.urandom(4).hex()}"

async def run_avatar_test():
    logging.info(f"🚀 Starting Avatar E2E Test (Room: {ROOM_NAME})")
    
    # 1. Metadata for Context Resolution
    metadata = {
        "mode": "avatar",
        "workspace_id": "wrk_debug_script",
        "agent_id": "agent_debug_script",
        "welcome_message": "Hello, I am your test avatar!"
    }

    # 2. Token with Agent Dispatch
    grant = api.VideoGrants(room_join=True, room=ROOM_NAME)
    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name="avatar-agent")]
    )
    
    token = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
             .with_grants(grant)
             .with_identity("verifier-avatar")
             .with_metadata(json.dumps(metadata))
             .with_room_config(room_config)
             .to_jwt())

    # 3. Connect Participant
    room = rtc.Room()
    
    agent_joined = asyncio.Event()
    greeting_received = asyncio.Event()
    disconnection_occurred = asyncio.Event()
    replica_joined = asyncio.Event()

    def check_for_agent():
        for p in room.remote_participants.values():
            if "agent" in str(p.kind).lower() or "agent" in p.identity.lower():
                logging.info(f"👋 Agent {p.identity} DETECTED.")
                agent_joined.set()
                return True
        return False

    @room.on("participant_connected")
    def on_participant_connected(p):
        is_agent = "agent" in str(p.kind).lower() or "agent" in p.identity.lower()
        if is_agent:
            logging.info(f"👋 Agent {p.identity} JOINED (event).")
            agent_joined.set()
        elif "standard" in str(p.kind).lower() and p.identity != "verifier-avatar":
            logging.info(f"📸 Replica {p.identity} JOINED.")
            replica_joined.set()

    @room.on("transcription_received")
    def on_transcription(segments, p, pub):
        text = " ".join([s.text for s in segments]).strip()
        if text:
            logging.info(f"📝 TRANSCRIPT ({p.identity}): {text}")
            greeting_received.set()

    @room.on("disconnected")
    def on_disconnected(_):
        logging.warning("⚠️ Room disconnected.")
        disconnection_occurred.set()

    try:
        await room.connect(LIVEKIT_URL, token)
        logging.info("✅ Verifier connected.")

        # Step A: Wait for Agent (Timeout 20s)
        logging.info("⏳ Waiting for Agent to join...")
        for i in range(20):
            if check_for_agent(): break
            await asyncio.sleep(1)
        
        if not agent_joined.is_set():
            logging.error("❌ FAILURE: Agent never joined.")
            return False

        # Step B: Wait for Transcription (Greeting) - Verifies Fix #2
        logging.info("⏳ Waiting for Greeting in transcript...")
        try:
            await asyncio.wait_for(greeting_received.wait(), timeout=15)
            logging.info("✅ GREETING RECEIVED in transcript.")
        except asyncio.TimeoutError:
            logging.error("❌ FAILURE: No greeting received in transcript.")
            return False

        # Step C: Stability Monitor (15s) - Verifies Fix #1 (1007 protocol)
        logging.info("🛡️ Monitoring stability for 15s...")
        for i in range(15):
            if disconnection_occurred.is_set():
                logging.error("❌ FAILURE: WebSocket dropped (likely 1007 error).")
                return False
            await asyncio.sleep(1)

        logging.info("🎉 AVATAR VERIFICATION PASSED!")
        return True

    finally:
        await room.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
    success = asyncio.run(run_avatar_test())
    exit(0 if success else 1)
