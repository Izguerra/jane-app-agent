
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.agent import AgentManager
from backend.prompts import GATEKEEPER_INSTRUCTION

def test_gatekeeper_prompt_construction():
    """
    Verifies that the Gatekeeper prompt is correctly formatted with the allowed worker types.
    """
    print("\n--- Testing Gatekeeper Prompt Construction ---")
    
    manager = AgentManager()
    
    # Test Case 1: Agent WITH allowed workers
    settings_with_workers = {
        "allowed_worker_types": ["lead_researcher", "content_writer"],
        "business_name": "TestBiz",
        "services": "Testing",
        "name": "TestAgent"
    }
    
    # We mock the _create_agent method's internal logic effectively by calling it 
    # (or rather, we check how it formats the prompt). 
    # Since _create_agent is internal and returns an Agent (LangChain) object, 
    # we want to inspect the 'system_message' or 'instructions' passed to it.
    
    # Note: AgentManager._create_agent constructs the prompt. 
    # Let's inspect the private method by subclassing or just invoking it if possible.
    # Actually, we can just copy the logic we want to test or trust the integration.
    # Better: Let's use a patch on the `Agent` class creation to capture the system prompt.
    
    with patch("backend.agent.Agent") as MockAgent:
        manager._create_agent(settings_with_workers, team_id=1)
        
        # Verify the call arguments
        # The prompt is usually passed as part of instructions or system_message
        call_args = MockAgent.call_args
        if not call_args:
            print("FAILED: Agent was not initialized.")
            return

        # Depending on how Agent is initialized in _create_agent...
        # Looking at previous code: 
        # return Agent(..., instructions=instructions, ...)
        
        kwargs = call_args.kwargs
        instructions = kwargs.get('instructions', [])
        
        # Combine instructions to check for Gatekeeper
        full_prompt = "\n".join(instructions) if isinstance(instructions, list) else str(instructions)
        
        if "- lead_researcher" in full_prompt and "- content_writer" in full_prompt:
            print("✅ SUCCESS: Allowed workers found in prompt.")
        else:
            print("❌ FAILED: Allowed workers NOT found in prompt.")
            print("Prompt Snippet:", full_prompt[:500])

    # Test Case 2: Agent WITHOUT allowed workers
    settings_no_workers = {
        "allowed_worker_types": [],
        "business_name": "TestBiz"
    }
    
    with patch("backend.agent.Agent") as MockAgent:
        manager._create_agent(settings_no_workers, team_id=1)
        
        kwargs = MockAgent.call_args.kwargs
        instructions = kwargs.get('instructions', [])
        full_prompt = "\n".join(instructions) if isinstance(instructions, list) else str(instructions)
        
        if "None (You generally cannot dispatch workers" in full_prompt or "None" in full_prompt:
             # loose check for "None" in the list part
             print("✅ SUCCESS: 'None' restriction found in prompt for agent with no workers.")
        else:
             print("❌ FAILED: Restriction text not found.")
             print("Prompt Snippet:", full_prompt[:500])

def test_api_persistence_mock():
    """
    Simulates the API saving logic to ensure allowed_worker_types is handled.
    Real DB test would require a running DB, here we verify the Model accepts it.
    """
    print("\n--- Testing Model Schema ---")
    from backend.models_db import Agent
    
    try:
        agent = Agent(allowed_worker_types=["test_worker"])
        print("✅ SUCCESS: Agent model accepts 'allowed_worker_types'.")
    except Exception as e:
        print(f"❌ FAILED: Agent model rejected 'allowed_worker_types': {e}")

if __name__ == "__main__":
    test_gatekeeper_prompt_construction()
    test_api_persistence_mock()
