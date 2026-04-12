import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

async def main():
    from backend.agents.orchestrator import AgentOrchestrator
    try:
        print("Testing Agno Email orchestration with logging...")
        res = await AgentOrchestrator.chat(
            message="I am Randy. My email is randy@supaagent.com. Please send me a test email right now with the subject 'Agno Stabilization' and message 'The email tool is now operational!'.",
            team_id="team_000V0qJzFzDqWqT2",
            workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J",
            agent_id="agnt_000VDh5hDA16wuQ5ZrX1EWkZZrk",
            stream=False
        )
        print("Chatbot execution response:")
        print(res)
    except Exception as e:
        print(f"Error testing chatbot email: {e}")

if __name__ == "__main__":
    asyncio.run(main())
