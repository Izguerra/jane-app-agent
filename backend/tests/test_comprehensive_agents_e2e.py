
import asyncio
import os
import json
import logging
import pytest
import httpx
from livekit import api, rtc
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

import jwt
from datetime import datetime, timezone, timedelta

# Use real IDs from DB discovered in previous step
AGENT_ID = "set_000V7emFAR1Qb8JnmNDzpNa4bXz"
WORKSPACE_ID = "wrk_000V7MkytiPCf7GFQzZN3O1K8O"
TEAM_ID = "org__000V7dCbbM1IPThV4WyCtrAh991" # Corrected team ID for workspace

AUTH_SECRET = os.getenv("AUTH_SECRET")
ALGORITHM = "HS256"

def create_access_token(user_id: str, team_id: str):
    payload = {
        "user": {
            "id": user_id,
            "teamId": team_id,
            "role": "admin"
        },
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=ALGORITHM)

# Use real token
ACCESS_TOKEN = create_access_token("dev_user_e2e", TEAM_ID)

BASE_URL = "http://localhost:8000" # Backend port

logger = logging.getLogger("comprehensive-e2e")

async def get_voice_token(mode: str = "voice", agent_id: str = AGENT_ID, workspace_id: str = WORKSPACE_ID):
    """Hits the real backend /voice/token endpoint to test initialization logic."""
    room_name = f"e2e-test-{mode}-{os.urandom(4).hex()}"
    async with httpx.AsyncClient() as client:
        # Pass the JWT token for authentication
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = await client.post(
            f"{BASE_URL}/voice/token",
            json={
                "room_name": room_name,
                "participant_name": f"tester-{mode}",
                "agent_id": agent_id,
                "workspace_id": workspace_id,
                "mode": mode
            },
            headers=headers,
            timeout=30 # Increased timeout
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
        
        data = response.json()
        data["room_name"] = room_name # Inject locally so test can use it
        return data

async def cleanup_room(room_name: str):
    """Hits the real backend /voice/cleanup-room endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = await client.post(
            f"{BASE_URL}/voice/cleanup-room",
            json={"room_name": room_name},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200

@pytest.mark.asyncio
async def test_cold_start_voice_connectivity():
    """Verify that a cold start voice call dispatches the agent and it joins."""
    print("\n--- Testing Cold Start Voice Connectivity ---")
    data = await get_voice_token(mode="voice")
    token = data["token"]
    room_name = data["room_name"]
    
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, token)
    print(f"Connected to room: {room_name}")
    
    # Wait for Agent to join
    timeout = 30
    start_time = asyncio.get_event_loop().time()
    agent_joined = False
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        if len(room.remote_participants) >= 1:
            agent_joined = True
            break
        await asyncio.sleep(2)
    
    assert agent_joined, "Voice agent failed to join the room on cold start."
    print("✅ Voice agent joined successfully.")
    await room.disconnect()
    await cleanup_room(room_name)

@pytest.mark.asyncio
async def test_cold_start_avatar_connectivity():
    """Verify that a cold start avatar call (Anam) dispatches and joins."""
    print("\n--- Testing Cold Start Avatar Connectivity ---")
    data = await get_voice_token(mode="avatar")
    token = data["token"]
    room_name = data["room_name"]
    
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, token)
    print(f"Connected to room: {room_name}")
    
    # Wait for Avatar Agent to join
    timeout = 45 # Avatar might take longer due to provider init
    start_time = asyncio.get_event_loop().time()
    agent_joined = False
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        # In avatar mode, we expect at least the agent worker to join.
        # The Anam/Tavus replica might show up as another participant.
        if len(room.remote_participants) >= 1:
            agent_joined = True
            break
        await asyncio.sleep(2)
    
    assert agent_joined, "Avatar agent failed to join the room on cold start."
    print("✅ Avatar agent joined successfully.")
    await room.disconnect()
    await cleanup_room(room_name)

@pytest.mark.asyncio
async def test_mode_switching_continuity():
    """Verify stability of switching from Voice -> Avatar and back."""
    print("\n--- Testing Mode Switching Continuity ---")
    
    # 1. Start Voice
    print(">> Initializing Voice Call...")
    voice_data = await get_voice_token(mode="voice")
    v_room_name = voice_data["room_name"]
    v_room = rtc.Room()
    await v_room.connect(LIVEKIT_URL, voice_data["token"])
    
    # Wait for voice agent
    await asyncio.sleep(5)
    assert len(v_room.remote_participants) >= 1, "Voice agent not found initially."
    print("✅ Voice agent online.")
    
    # 2. Cleanup Voice
    print(">> Cleaning up Voice Call...")
    await v_room.disconnect()
    await cleanup_room(v_room_name)
    
    # 3. Start Avatar
    print(">> Switching to Avatar Call...")
    avatar_data = await get_voice_token(mode="avatar")
    a_room_name = avatar_data["room_name"]
    a_room = rtc.Room()
    await a_room.connect(LIVEKIT_URL, avatar_data["token"])
    
    # Wait for avatar agent
    success = False
    for _ in range(15):
        if len(a_room.remote_participants) >= 1:
            success = True
            break
        await asyncio.sleep(2)
    
    assert success, "Avatar agent failed to join after switching from voice."
    print("✅ Avatar agent switched successfully.")
    
    await a_room.disconnect()
    await cleanup_room(a_room_name)

@pytest.mark.asyncio
async def test_tool_injection_verification():
    """
    Verifies that the agent initialization log contains the expected tool count,
    proving that WorkerTools/AgentTools are injected correctly.
    """
    print("\n--- Verifying Tool Injection via Logs ---")
    # This test reads the most recent log line for initialization
    log_path = "voice_agent_restart.log"
    if not os.path.exists(log_path):
        pytest.skip("voice_agent_restart.log not found, cannot verify tools.")
    
    # Trigger a real connection to ensure the agent reaches the tool loading phase
    data = await get_voice_token(mode="voice")
    token = data["token"]
    room_name = data["room_name"]
    
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, token)
    print(f"Connected to room {room_name} for log verification...")
    
    # Wait for agent to join (which triggers tool loading)
    for _ in range(10):
        if len(room.remote_participants) >= 1:
            break
        await asyncio.sleep(2)
    
    await room.disconnect()
    await cleanup_room(room_name)
    
    await asyncio.sleep(3) # Give log time to flush
    
    found_tool_log = False
    with open(log_path, "rb") as f:
        # Read last 2000 bytes and decodes with errors='ignore'
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - 10000))
        lines = f.read().decode('utf-8', errors='ignore').splitlines()
        
        for line in reversed(lines):
            if "Loading" in line and "tools for Voice Agent" in line:
                print(f"Found tool log: {line.strip()}")
                # Expected: "Loading X tools for Voice Agent (Filtered by skills)"
                # We want X > 0
                parts = line.split("Loading ")
                if len(parts) > 1:
                    count_str = parts[1].split(" ")[0]
                    try:
                        count = int(count_str)
                        assert count > 0, f"No tools were loaded! Log: {line}"
                        print(f"✅ Verified {count} tools injected.")
                        found_tool_log = True
                        break
                    except ValueError: pass
    
    assert found_tool_log, "Could not find tool-loading confirmation in logs."

if __name__ == "__main__":
    pytest.main([__file__])
