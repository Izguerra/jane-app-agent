import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()
# Set up logging to show the tool execution flow
logging.basicConfig(level=logging.INFO)
# Suppress some noisy logs from dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)

async def main():
    from backend.agents.orchestrator import AgentOrchestrator
    try:
        print("\n=== STARTING COMBINED CHATBOT SKILLS TEST ===")
        print("Target: SMS to 4167865786, Email to randy@supaagent.com")
        
        message = (
            "Hi, I am calling on behalf of Randy. "
            "1. Please send an SMS to 4167865786 saying 'Chatbot skills test: SMS is working!'. "
            "2. Also, send an email to randy@supaagent.com with subject 'Skills Verification' "
            "and body 'Chatbot skills test: Email tool is confirmed operational!'. "
            "Please confirm once both are done."
        )
        
        res = await AgentOrchestrator.chat(
            message=message,
            team_id="team_000V0qJzFzDqWqT2",
            workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J",
            agent_id="agnt_000VDh5hDA16wuQ5ZrX1EWkZZrk",
            stream=False
        )
        
        print("\n=== CHATBOT FINAL RESPONSE ===")
        print(res)
        print("\n=== TEST COMPLETE ===")
        
    except Exception as e:
        print(f"Error during combined test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
