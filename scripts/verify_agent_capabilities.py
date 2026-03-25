
import os
import sys
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Agent, Workspace
from backend.agent import AgentManager
from backend.services.acknowledgement_service import stream_with_followup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-capabilities")

async def test_agent_manager_methods():
    print("\n--- Test 1: AgentManager Method Restoration ---")
    manager = AgentManager()
    if hasattr(manager, "_create_agent"):
        print("✅ AgentManager has _create_agent")
    else:
        print("❌ AgentManager is missing _create_agent")
        return False
    
    if hasattr(manager, "create_agent"):
        print("✅ AgentManager has create_agent(alias)")
    else:
        print("❌ AgentManager is missing create_agent")
        return False
    return True

async def test_prompt_enrichment():
    print("\n--- Test 2: Voice/Avatar Prompt Enrichment ---")
    db = SessionLocal()
    try:
        agent = db.query(Agent).first()
        if not agent:
            print("⚠️ No agent found in DB, skipping prompt test")
            return True
        
        # Manually set some worker types to test
        settings = {
            "allowed_worker_types": ["lead-research", "content-writer"],
            "agent_type": "business",
            "business_name": "Test Business"
        }
        print(f"Testing with workers: {settings['allowed_worker_types']}")
        
        from backend.services.voice_prompt_builder import VoicePromptBuilder
        prompt = VoicePromptBuilder.build_prompt(
            settings=settings,
            personality_prompt="Be helpful.",
            enabled_skills=[],
            workspace_info={"name": "Test Workspace", "phone": "123"},
            current_datetime_str="2026-03-24",
            client_location="Toronto"
        )
        
        # Check if the prompt contains instructions for the tools
        success = True
        if "lead-research" in prompt.lower() or "research" in prompt.lower():
            print("✅ Prompt contains research instructions")
        else:
            print("❌ Prompt MISSING research instructions")
            success = False
            
        if "content-writer" in prompt.lower() or "writer" in prompt.lower():
            print("✅ Prompt contains content-writer instructions")
        else:
            print("❌ Prompt MISSING writer instructions")
            success = False
            
        return success
    finally:
        db.close()

async def test_streaming_logic():
    print("\n--- Test 3: Chatbot Streaming Consistency ---")
    
    async def mock_generator():
        yield "Hello"
        await asyncio.sleep(0.5)
        yield " World"
        await asyncio.sleep(0.1)
        yield "!"
        
    chunks = []
    try:
        async for chunk in stream_with_followup(mock_generator(), "Ack"):
            chunks.append(chunk)
            print(f"Stream yielded: '{chunk}'")
        
        full_text = "".join(chunks)
        if "Hello World!" in full_text:
            print("✅ Streaming logic preserved original content")
        else:
            print(f"❌ Streaming logic corrupted content: {full_text}")
            return False
        return True
    except Exception as e:
        print(f"❌ Streaming logic CRASHED: {e}")
        return False

async def main():
    s1 = await test_agent_manager_methods()
    s2 = await test_prompt_enrichment()
    s3 = await test_streaming_logic()
    
    print("\n--- Verification Summary ---")
    if s1 and s2 and s3:
        print("🚀 ALL SYSTEMS GO! Agent stabilization successful.")
    else:
        print("⚠️ Some systems failed verification. Check logs above.")

if __name__ == "__main__":
    asyncio.run(main())
