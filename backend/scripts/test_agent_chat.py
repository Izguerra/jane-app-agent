
import asyncio
import os
import sys

sys.path.append(os.getcwd())

from backend.agent import AgentManager

async def test_agent_chat():
    print("--- TESTING AGENT CHAT DIRECTLY ---")
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    agent_manager = AgentManager()
    
    # We need a team_id. Using 1 as a fallback or fetching from DB
    team_id = 1 
    
    # Pass explicit config
    config = {
        "name": "Test Agent",
        "allowed_worker_types": [],
        "creativity_level": 50
    }
    
    print("Sending message: 'Hello, are you Liquid AI?'")
    try:
        response = await agent_manager.chat(
            message="Hello, are you Liquid AI?",
            team_id="1", 
            workspace_id=workspace_id,
            agent_config=config
        )
        print("\n✅ AGENT RESPONSE:")
        print(response)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_chat())
