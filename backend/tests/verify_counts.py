
import asyncio
import os
import json
import jwt
from datetime import datetime, timezone, timedelta
from livekit import api, rtc
from dotenv import load_dotenv
import httpx

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
AUTH_SECRET = os.getenv("AUTH_SECRET")
AGENT_ID = "ag_000VEgO60m6T9yX1lXitbC0XhYq" # Placeholder, will be resolved by get_settings
WORKSPACE_ID = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
TEAM_ID = "org_000V7dMzThAVrPNF3XBlRXq4MO"

def create_access_token():
    payload = {"user": {"id": "tester", "teamId": TEAM_ID, "role": "admin"}, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    return jwt.encode(payload, AUTH_SECRET, algorithm="HS256")

async def test_counts(mode):
    print(f"\n--- Testing {mode.upper()} Count ---")
    headers = {"Authorization": f"Bearer {create_access_token()}"}
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/voice/token", json={
            "room_name": f"count-test-{mode}", "agent_id": AGENT_ID, "workspace_id": WORKSPACE_ID, "mode": mode
        }, headers=headers, timeout=30)
        data = res.json()
    
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, data["token"])
    print(f"Connected to {mode} room.")
    
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < 30:
        total = len(room.remote_participants) + 1
        identities = [p.identity for p in room.remote_participants.values()]
        print(f"[{int(asyncio.get_event_loop().time() - start_time)}s] Participants ({total}): {['self'] + identities}")
        
        # Target: Voice=2, Avatar=3
        target = 2 if mode == "voice" else 3
        if total >= target:
            print(f"✅ Reached target count of {target}!")
            break
        await asyncio.sleep(2)
    
    await room.disconnect()

async def main():
    await test_counts("voice")
    await asyncio.sleep(5)
    await test_counts("avatar")

if __name__ == "__main__":
    asyncio.run(main())
