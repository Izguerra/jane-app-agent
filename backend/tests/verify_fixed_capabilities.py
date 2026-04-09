
import asyncio
import os
import json
import logging
import subprocess
import time
import sys
from livekit import api, rtc
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("e2e-verify")

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

PYTHON_EXEC = "./venv/bin/python" if os.path.exists("./venv/bin/python") else sys.executable

async def run_scenario(name, mode, settings):
    logger.info(f"\n{'='*20}\nSCENARIO: {name}\n{'='*20}")
    
    room_name = f"verify-{mode}-{os.urandom(3).hex()}"
    test_agent_name = f"test-agent-{mode}-{os.urandom(2).hex()}"
    agent_script = "backend/voice_agent.py" if mode == "voice" else "backend/avatar_agent.py"
    log_path = f"backend/worker_verify_{mode}.log"
    
    # Valid IDs for testing
    VALID_WORKSPACE_ID = "wrk_000V8OiPKcNMw3AKAOk045kpQZ"
    VALID_ANAM_PERSONA = "edf6fdcb-acab-44b8-b974-ded72665ee26"
    
    # 1. Start Worker with unique agent name
    logger.info(f">> Starting {mode} agent worker as '{test_agent_name}'...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.getcwd()
    env["LIVEKIT_AGENT_NAME"] = test_agent_name
    
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(
            [PYTHON_EXEC, agent_script, "start"],
            env=env,
            stdout=log_file,
            stderr=log_file
        )
    
    try:
        # 2. Setup LiveKit Token & Room
        logger.info(f">> Generating token for room: {room_name}")
        room_config = api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name=test_agent_name)]
        )
        grant = api.VideoGrants(room_join=True, room=room_name)
        grant.can_publish = True
        
        # Inject metadata to simulate user settings
        metadata = json.dumps({
            "workspace_id": VALID_WORKSPACE_ID,
            "voice_id": settings.get("voice_id", "aura-orion-en"),
            "avatar_provider": settings.get("avatar_provider", "anam"),
            "persona_id": VALID_ANAM_PERSONA if settings.get("avatar_provider") == "anam" else "persona_123"
        })
        
        token = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(f"tester-{os.urandom(2).hex()}")
            .with_grants(grant)
            .with_metadata(metadata)
            .with_room_config(room_config)
            .to_jwt()
        )

        # 3. Connect as "User" and wait for agent
        logger.info(f">> Connecting to LiveKit...")
        room = rtc.Room()
        await room.connect(LIVEKIT_URL, token)
        
        logger.info(f">> Waiting for agent to join {room_name}...")
        expected = settings.get("target_participants", 2)
        success = False
        
        # Wait up to 60s for agent to join and initialize
        for i in range(30):
            count = len(room.remote_participants) + 1 # +1 for local tester
            remote_ids = [p.identity for p in room.remote_participants.values()]
            logger.info(f"[{i*2}s] Count: {count} | Remote: {remote_ids}")
            
            if count >= expected:
                logger.info(f"✅ Reached expected participant count: {count}")
                success = True
                break
            await asyncio.sleep(2)
        
        if not success:
            logger.error(f"❌ Timeout waiting for target participant count ({expected}). Reached: {len(room.remote_participants)+1}")
        
        # 4. Check Logs for Markers
        await asyncio.sleep(5) # Give some time for initialization logs to flush
        marker = settings.get("marker")
        if marker:
            with open(log_path, "r") as f:
                logs = f.read()
                if marker.lower() in logs.lower():
                    logger.info(f"✅ FOUND log marker: '{marker}'")
                else:
                    logger.error(f"❌ MISSING log marker: '{marker}'")
                    # Log snippet for debugging
                    logger.error(f"--- LOG SNIPPET ---\n{logs[-500:]}\n--- END ---")
                    success = False

        if success:
            logger.info(f"✨ SCENARIO {name} PASSED! ✨")
        else:
            logger.error(f"💥 SCENARIO {name} FAILED! 💥")
        
        return success

    finally:
        logger.info(">> Cleaning up worker...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()
        await room.disconnect()
                
async def main():
    results = []
    
    # Test 1: Voice - ElevenLabs Adam
    res1 = await run_scenario(
        "Voice with ElevenLabs Adam",
        "voice",
        {
            "voice_id": "Adam", 
            "target_participants": 2,
            "marker": "Initializing ElevenLabs TTS (Adam)"
        }
    )
    results.append(("Voice ElevenLabs", res1))

    # Test 2: Voice - Deepgram Aura Orion
    res2 = await run_scenario(
        "Voice with Deepgram Aura Orion",
        "voice",
        {
            "voice_id": "aura-orion-en", 
            "target_participants": 2,
            "marker": "Initializing Deepgram Aura TTS (aura-orion-en)"
        }
    )
    results.append(("Voice Deepgram", res2))

    # Test 3: Avatar - Anam.ai with OpenAI Alloy
    res3 = await run_scenario(
        "Avatar with Anam.ai and OpenAI Alloy",
        "avatar",
        {
            "avatar_provider": "anam", 
            "voice_id": "alloy",
            "target_participants": 3,
            "marker": "Initializing OpenAI TTS (alloy) with 1.15x speed for avatar"
        }
    )
    results.append(("Avatar Anam", res3))

    logger.info("\n" + "="*30)
    logger.info("FINAL VERIFICATION SUMMARY")
    logger.info("="*30)
    all_ok = True
    for name, res in results:
        status = "PASSED" if res else "FAILED"
        logger.info(f"{name:25}: {status}")
        if not res: all_ok = False
        
    if all_ok:
        logger.info("\n✅ ALL END-TO-END TESTS PASSED SUCESSFULLY! ✅")
        sys.exit(0)
    else:
        logger.error("\n❌ SOME E2E TESTS FAILED. ❌")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
