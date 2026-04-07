import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from backend.utils.multimodal_agent import MultimodalAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-fix")

async def test_agent_start_signature():
    """
    Verifies that MultimodalAgent.start() calls AgentSession.start()
    with the correct arguments (room and room_options, No voice_agent).
    """
    logger.info("Testing MultimodalAgent.start() signature fix...")
    
    # Mock dependencies
    mock_room = MagicMock()
    mock_model = MagicMock()
    # Ensure model is treated as native audio (multimodal)
    mock_model.__class__ = MagicMock
    from livekit.agents import llm
    mock_model.__class__ = llm.RealtimeModel
    
    agent = MultimodalAgent(
        model=mock_model,
        workspace_id="test_ws",
        voice_id="test_voice",
        fnc_ctx=None,
        prompt="Test prompt"
    )
    
    # Mock AgentSession
    mock_session = AsyncMock()
    agent._session = mock_session
    
    # Trigger start
    try:
        # We need to bypass the _voice_agent creation or mock it
        agent._voice_agent = MagicMock()
        agent._voice_agent.stt = None
        agent._voice_agent.tts = None
        
        await agent.start(mock_room)
        logger.info("Successfully called agent.start(room)")
        
        # Verify the call to the underlying session.start
        mock_session.start.assert_called_once()
        args, kwargs = mock_session.start.call_args
        
        logger.info(f"session.start called with args: {args}, kwargs: {kwargs.keys()}")
        
        if 'voice_agent' in kwargs:
            logger.error("FAILED: 'voice_agent' still passed to session.start()")
            return False
        
        if args[0] != mock_room:
            logger.error("FAILED: 'room' not passed as first argument to session.start()")
            return False
            
        logger.info("PASSED: session.start() called with correct signature.")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_agent_start_signature())
