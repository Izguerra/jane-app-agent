import asyncio
import os
import sys
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models_db import Agent
from backend.services.vector_sync import sync_agent_soul
from backend.settings_store import get_settings

async def verify_soul_sync():
    db = SessionLocal()
    try:
        # Find an agent to test with
        agent = db.query(Agent).first()
        if not agent:
            print("No agent found in database.")
            return

        print(f"Testing with Agent: {agent.name} ({agent.id})")
        
        # 1. Verify get_settings now includes 'soul'
        settings = get_settings(agent.workspace_id)
        print(f"Settings 'soul' exists: {'soul' in settings}")
        
        # 2. Directly test sync_agent_soul
        test_soul = "This is a test soul for binary verification of Pinecone sync."
        print(f"Triggering sync for soul: {test_soul[:30]}...")
        
        # Mocking KB service check if needed, but we want to see the logger output
        sync_agent_soul(agent.workspace_id, agent.id, test_soul)
        
        print("Sync triggered. Please check backend logs for 'Synced agent soul to vector db'.")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_soul_sync())
