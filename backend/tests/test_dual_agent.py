import asyncio
import os
import logging
from livekit import api
from livekit import rtc
from dotenv import load_dotenv

# Load env
load_dotenv(dotenv_path=".env")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    print(f"Error: LiveKit credentials not found in .env. Checked: {os.path.abspath('.env')}")
    # Try print keys present
    # print(f"Keys: {os.environ.keys()}")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_dual_agent")

async def test_agent_connection(agent_script, room_name, dispatch_rule):
    logger.info(f"--- Testing {agent_script} in {room_name} ---")
    
    # 1. Create Token for User with Agent Dispatch
    room_config = api.RoomConfiguration(agents=[dispatch_rule])

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("test-user")
        .with_name("Test User")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .with_room_config(room_config) # Dispatch agent!
        .to_jwt()
    )

    # 2. Start Agent Process
    logger.info(f"Starting agent process: {agent_script}")
    # We need to pass the room name? Or does the agent auto-dispatch?
    # Usually agents listen to ALL rooms or specific ones.
    # If using 'dev' mode, they typically join a pre-defined room or we need to ensure they join THIS room.
    # For `avatar_agent.py` and `voice_agent.py`, they likely use `JobRequest` (Worker).
    # So we need to CREATE a room, which triggers a webhook? Or manually connect?
    
    # In 'dev' mode (python backend/voice_agent.py dev), it typically connects to a room automatically or waits?
    # Let's assume we run them in 'dev' mode which connects to a room if a user joins.
    
    agent_process = await asyncio.create_subprocess_exec(
        "python", agent_script, "dev",
        env={**os.environ, "LIVEKIT_URL": LIVEKIT_URL},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        # 3. Connect to Room
        room = rtc.Room()
        logger.info(f"Connecting to room {room_name}...")
        await room.connect(LIVEKIT_URL, token)
        logger.info("User connected!")

        # 4. Wait for Agent (Second Participant)
        logger.info("Waiting for agent to join...")
        agent_joined = False
        
        # Check existing
        if len(room.remote_participants) > 0:
            logger.info(f"Agent already present: {room.remote_participants}")
            agent_joined = True

        if not agent_joined:
            # Wait for event
            try:
                # Simple polling for this test
                for _ in range(20): # Wait 20 seconds
                    await asyncio.sleep(1)
                    if len(room.remote_participants) > 0:
                        logger.info(f"Participant joined! Total: {len(room.remote_participants) + 1}")
                        agent_joined = True
                        break
            except Exception as e:
                logger.error(f"Waiting failed: {e}")

        if agent_joined:
            logger.info("SUCCESS: 2 Participants in room.")
            # Verify audio track?
            # p = list(room.remote_participants.values())[0]
            # ...
        else:
            logger.error("FAILURE: Agent did not join.")
            # Print agent output for debugging
            if agent_process:
                try:
                    stdout, stderr = await asyncio.wait_for(agent_process.communicate(), timeout=2.0)
                    if stdout: logger.info(f"AGENT STDOUT:\n{stdout.decode()}")
                    if stderr: logger.error(f"AGENT STDERR:\n{stderr.decode()}")
                except Exception as e:
                    logger.error(f"Could not capture logs: {e}")
        
        await room.disconnect()

    finally:
        if agent_process:
            logger.info("Terminating agent process...")
            try:
                agent_process.terminate()
                await asyncio.wait_for(agent_process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                logger.warning("Agent process did not terminate, killing...")
                agent_process.kill()
                await agent_process.wait()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            logger.info("Agent process terminated.")

async def main():
    # Test Standard Agent
    room_std = f"test-std-{os.urandom(4).hex()}"
    print(f"Testing Standard Agent connection to room: {room_std}")
    std_dispatch = api.RoomAgentDispatch(agent_name="supaagent-voice-agent")
    await test_agent_connection("backend/voice_agent.py", room_std, std_dispatch)
    
    print("\n" + "="*30 + "\n")
    
    # Test OpenClaw Agent
    room_claw = f"test-claw-{os.urandom(4).hex()}"
    print(f"Testing OpenClaw/Avatar Agent connection to room: {room_claw}")
    avatar_dispatch = api.RoomAgentDispatch(agent_name="supaagent-avatar-agent")
    await test_agent_connection("backend/avatar_agent.py", room_claw, avatar_dispatch)

if __name__ == "__main__":
    asyncio.run(main())
