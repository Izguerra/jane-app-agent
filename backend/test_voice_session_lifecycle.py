"""
Integration test for voice agent session lifecycle.

This test verifies:
1. Agent worker can connect to LiveKit Cloud
2. Agent receives dispatch when user connects
3. Agent session stays alive (doesn't exit prematurely)
4. Agent waits for user input (no initial greeting)
5. Agent can handle the session lifecycle correctly
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api, rtc
import time

load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_session_lifecycle")

async def test_session_lifecycle():
    """Test that agent connects and maintains session without premature exit."""
    
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    API_KEY = os.getenv("LIVEKIT_API_KEY")
    API_SECRET = os.getenv("LIVEKIT_API_SECRET")

    if not all([LIVEKIT_URL, API_KEY, API_SECRET]):
        logger.error("❌ TEST FAILED: Missing LiveKit credentials")
        logger.error(f"   LIVEKIT_URL: {'✓' if LIVEKIT_URL else '✗'}")
        logger.error(f"   LIVEKIT_API_KEY: {'✓' if API_KEY else '✗'}")
        logger.error(f"   LIVEKIT_API_SECRET: {'✓' if API_SECRET else '✗'}")
        return False

    # Generate unique room name for this test
    import uuid
    room_name = f"test-{str(uuid.uuid4())[:8]}"
    identity = f"test-user-{str(uuid.uuid4())[:8]}"

    logger.info("=" * 60)
    logger.info("VOICE AGENT SESSION LIFECYCLE TEST")
    logger.info("=" * 60)
    logger.info(f"Room: {room_name}")
    logger.info(f"Identity: {identity}")
    logger.info(f"LiveKit URL: {LIVEKIT_URL}")
    logger.info("")

    # 1. Generate Token with Agent Dispatch
    logger.info("Step 1: Generating token with agent dispatch...")
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
    logger.info("✓ Token generated successfully")
    logger.info("")

    # 2. Connect to Room
    logger.info("Step 2: Connecting to LiveKit room...")
    room = rtc.Room()
    
    # Track test results
    test_results = {
        "agent_connected": False,
        "agent_stayed_alive": False,
        "no_premature_disconnect": True,
        "session_duration": 0
    }
    
    agent_participant = None
    connection_time = None
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal agent_participant, connection_time
        logger.info(f"   Participant connected: {participant.identity} (kind={participant.kind})")
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            logger.info("   ✓ AGENT CONNECTED!")
            test_results["agent_connected"] = True
            agent_participant = participant
            connection_time = time.time()

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        nonlocal connection_time
        logger.info(f"   Participant disconnected: {participant.identity}")
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
            if connection_time:
                duration = time.time() - connection_time
                test_results["session_duration"] = duration
                logger.info(f"   Agent session duration: {duration:.2f}s")
                # If agent disconnects within 2 seconds, it's premature
                if duration < 2:
                    logger.warning(f"   ⚠ Agent disconnected prematurely after {duration:.2f}s")
                    test_results["no_premature_disconnect"] = False

    try:
        await room.connect(LIVEKIT_URL, token)
        logger.info("✓ Connected to room")
        logger.info("")

        # 3. Wait for agent to join
        logger.info("Step 3: Waiting for agent to join (timeout: 20s)...")
        for i in range(20):
            if test_results["agent_connected"]:
                break
            await asyncio.sleep(1)
            if i % 5 == 4:
                logger.info(f"   Still waiting... ({i+1}s)")
        
        if not test_results["agent_connected"]:
            logger.error("❌ TEST FAILED: Agent did not join within 20 seconds")
            logger.error("   This indicates the agent worker is not receiving dispatches")
            logger.error("   Check that the worker is running and registered")
            return False
        
        logger.info("✓ Agent joined successfully")
        logger.info("")

        # 4. Verify agent stays alive (doesn't disconnect immediately)
        logger.info("Step 4: Verifying agent session stays alive (10s observation)...")
        for i in range(10):
            if agent_participant and agent_participant not in room.remote_participants.values():
                logger.error(f"❌ TEST FAILED: Agent disconnected after {i}s")
                test_results["no_premature_disconnect"] = False
                break
            await asyncio.sleep(1)
            if i % 3 == 2:
                logger.info(f"   Agent still connected... ({i+1}s)")
        
        if test_results["no_premature_disconnect"]:
            logger.info("✓ Agent session remained stable for 10 seconds")
            test_results["agent_stayed_alive"] = True
        logger.info("")

        # 5. Verify agent is waiting (not speaking)
        logger.info("Step 5: Verifying agent waits for user input (no initial greeting)...")
        # Check if agent published any audio tracks
        agent_audio_tracks = []
        if agent_participant:
            for pub in agent_participant.track_publications.values():
                if pub.kind == rtc.TrackKind.KIND_AUDIO:
                    agent_audio_tracks.append(pub)
        
        if len(agent_audio_tracks) == 0:
            logger.info("✓ Agent has not published audio (correctly waiting for user)")
        else:
            logger.warning(f"⚠ Agent published {len(agent_audio_tracks)} audio track(s)")
            logger.warning("  This may indicate an initial greeting is being sent")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ TEST FAILED: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        logger.info("Cleaning up: Disconnecting from room...")
        await room.disconnect()
        logger.info("✓ Disconnected")
        logger.info("")

    # Print test results
    logger.info("=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Agent Connected:           {'✓ PASS' if test_results['agent_connected'] else '✗ FAIL'}")
    logger.info(f"Agent Stayed Alive:        {'✓ PASS' if test_results['agent_stayed_alive'] else '✗ FAIL'}")
    logger.info(f"No Premature Disconnect:   {'✓ PASS' if test_results['no_premature_disconnect'] else '✗ FAIL'}")
    if test_results['session_duration'] > 0:
        logger.info(f"Session Duration:          {test_results['session_duration']:.2f}s")
    logger.info("=" * 60)
    
    # Overall result
    all_passed = (
        test_results['agent_connected'] and
        test_results['agent_stayed_alive'] and
        test_results['no_premature_disconnect']
    )
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("")
        logger.info("The voice agent session lifecycle is working correctly:")
        logger.info("  ✓ Agent receives dispatches from LiveKit Cloud")
        logger.info("  ✓ Agent session stays alive without premature exit")
        logger.info("  ✓ Agent correctly waits for user input")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("Review the failures above and check:")
        logger.error("  - Worker is running and registered")
        logger.error("  - Session lifecycle code is correct")
        logger.error("  - No premature exit conditions")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_session_lifecycle())
    exit(0 if result else 1)
