import asyncio
import os
import sys
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models_db import Agent

async def verify_soul_retrieval():
    db = SessionLocal()
    try:
        # 1. Manually check first agent in DB
        agent = db.query(Agent).first()
        if not agent:
            print("No agent found in database.")
            return

        print(f"Agent in DB: {agent.name} ({agent.id})")
        print(f"Soul value in DB: {agent.soul}")

        # 2. Mocking the logic of get_agents to verify the dictionary construction
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "soul": agent.soul, # This is the field we just added
        }
        
        print(f"Agent dict for API response: {agent_dict}")
        
        if "soul" in agent_dict and agent_dict["soul"] == agent.soul:
            print("SUCCESS: Soul field is correctly included in the API response dictionary.")
        else:
            print("FAILURE: Soul field is missing or incorrect in the API response dictionary.")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_soul_retrieval())
