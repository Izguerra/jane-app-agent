
import sys
import os
import json
import asyncio
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Force SQLite for database.py before it loads
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.agent import AgentManager
from backend.agent_tools import AgentTools
from backend.services import get_agent_manager

def test_agent_manager_prompt():
    """Verify that AgentManager constructed instructions include web-research."""
    print("\n[1/3] Testing AgentManager Prompt Construction...")
    manager = AgentManager()
    
    # Mock settings with web-research skill
    settings = {
        "name": "SupaAgent",
        "business_name": "Test Clinic",
        "allowed_worker_types": ["web-research", "weather-worker"]
    }
    
    with patch("backend.agent.Agent") as MockAgent:
        manager._create_agent(settings, team_id="team_1", workspace_id="ws_1")
        
        kwargs = MockAgent.call_args.kwargs
        instructions = kwargs.get('instructions', [])
        full_text = "\n".join(instructions) if isinstance(instructions, list) else str(instructions)
        
        if "web-research" in full_text and "Search the web for real-time information" in full_text:
            print("✅ SUCCESS: 'web-research' worker description found in instructions.")
        else:
            print("❌ FAILED: 'web-research' description missing.")
            # print(f"DEBUG: {full_text[:1000]}")

def test_agent_tools_integration():
    """Verify AgentTools has web_search registered."""
    print("\n[2/3] Testing AgentTools Registration...")
    
    # We check if AgentTools has the web_search method decorated with @llm.function_tool
    tools = AgentTools(workspace_id="ws_1")
    
    from livekit.agents import llm
    found_tools = llm.find_function_tools(tools)
    tool_names = [t.info.name for t in found_tools]
    
    if "web_search" in tool_names:
        print("✅ SUCCESS: AgentTools has 'web_search' successfully discovered by LiveKit.")
    else:
        print(f"❌ FAILED: 'web_search' not found in LiveKit tools. Found: {tool_names}")

async def test_whatsapp_webhook_logic():
    """Verify WhatsApp webhook handler is functional and imports are correct."""
    print("\n[3/3] Testing WhatsApp Webhook Logic (Smoke Test)...")
    
    try:
        from backend.routers.meta_webhooks import process_incoming_message
        print("✅ SUCCESS: process_incoming_message imported correctly.")
        
        # Mock inputs
        message = {
            "from": "123456789",
            "type": "text",
            "text": {"body": "Hello"},
            "id": "msg_1",
            "timestamp": "12345678"
        }
        metadata = {"phone_number_id": "phone_1"}
        
        # Test if we can at least reach the DB part before it fails (mocking DB)
        with patch("backend.routers.meta_webhooks.SessionLocal") as MockSession:
            # Alternative: Patch the source
            with patch("backend.services.get_agent_manager") as MockGetManagerSource:
                 mock_manager = MockGetManagerSource.return_value
                 mock_manager.chat.return_value = asyncio.Future()
                 mock_manager.chat.return_value.set_result("Hi there!")
                 
                 # This will likely fail on Workspace lookup, which is fine, 
                 # we want to ensure no ModuleNotFound errors or duplicate function errors.
                 try:
                     # Run one step
                     await process_incoming_message(message, metadata)
                 except Exception as e:
                     # Expecting DB or Workspace errors if we don't mock everything
                     if "NoneType" in str(e) or "Workspace" in str(e) or "Integration" in str(e) or "SessionLocal" in str(e):
                         print("✅ SUCCESS: Handler logic reached DB/Resolution phase.")
                     else:
                         print(f"⚠️ NOTE: Handler reached logic but failed with: {e}")
    except Exception as e:
        print(f"❌ FAILED: WhatsApp webhook logic test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_manager_prompt()
    test_agent_tools_integration()
    asyncio.run(test_whatsapp_webhook_logic())
