import asyncio
import os
import aiohttp
import logging
from livekit import rtc
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-client-test")
load_dotenv()

import jwt
import time

SERVER_URL = "http://127.0.0.1:8000"

def generate_test_token():
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        raise ValueError("AUTH_SECRET not found in .env")
    
    payload = {
        "user": {
            "id": "test-user-id",
            "teamId": "org__000V7dCbbM1IPThV4WyCtrAh991",
            "name": "Test User",
            "role": "admin"
        },
        "email": "test@example.com",
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, secret, algorithm="HS256")

async def test_avatar_flow():
    token_jwt = generate_test_token()
    headers = {"Authorization": f"Bearer {token_jwt}"}

    # 1. Get Token
    async with aiohttp.ClientSession() as session:
        # Mimic valid request payload
        payload = {
            "mode": "avatar",
            "agent_id": None, # Uses default settings
            "tavus_replica_id": "rfcc944ac6", # Use a known valid ID (Steph)
            "tavus_persona_id": "p7fb0be3", # Use a known valid ID
        }
        
        logger.info(f"Requests token from {SERVER_URL}/voice/token...")
        async with session.post(f"{SERVER_URL}/voice/token", json=payload, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"Failed to get token: {resp.status} - {text}")
                return
            
            data = await resp.json()
            token = data["token"]
            ws_url = data["url"]
            logger.info("Token received.")

    # 2. Connect to LiveKit
    logger.info(f"Connecting to LiveKit Room at {ws_url}...")
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"PARTICIPANT CONNECTED: {participant.identity} ({participant.name})")

    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"TRACK SUBSCRIBED: {track.kind} from {participant.identity}")

    try:
        await room.connect(ws_url, token)
        logger.info(f"Connected to room: {room.name}")
        
        # Check existing participants
        for p in room.remote_participants.values():
            logger.info(f"Existing Participant: {p.identity} ({p.name})")
            
        logger.info("Waiting 30 seconds for Agent to join...")
        await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"Connection Failed: {e}")
    finally:
        await room.disconnect()
        logger.info("Disconnected")

if __name__ == "__main__":
    asyncio.run(test_avatar_flow())
