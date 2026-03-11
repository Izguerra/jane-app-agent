
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from backend.database import SessionLocal
from backend.models_db import Workspace, Agent, Skill, AgentSkill

def check():
    db = SessionLocal()
    try:
        workspace_id = "wrk_000V7MzXJLzP5mYgdf7FzjA3J" # Wait, I previously used wrk_000V7dMzXJLzP5mYgdf7FzjA3J
        # Let's search again for the EXACT id from the grep result
        # ./agent_restart.log: ... wrk_000V7dMzXJLzP5mYgdf7FzjA3J
        workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
        print(f"Checking Workspace: {workspace_id}")
        
        agents = db.query(Agent).filter(Agent.workspace_id == workspace_id).all()
        for agent in agents:
            if agent.name == "Sarah":
                print(f"\n--- Agent: {agent.name} ({agent.id}) ---")
                print(f"RAW settings JSONB: {agent.settings}")
                print(f"allowed_worker_types Column: {agent.allowed_worker_types}")

    finally:
        db.close()

if __name__ == "__main__":
    check()
