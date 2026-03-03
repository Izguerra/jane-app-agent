import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import sys
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Agent

async def update_agent():
    db = SessionLocal()
    
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    # CORRECTED ID with lowercase 'oo'
    agent_id = "agnt_000VA6fCM7ooHx7VALTwm40ed8"
    instance_id = "e398a7a1-5496-455b-8ba2-21134df13b84"
    
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            settings = agent.settings or {}
            settings["open_claw_instance_id"] = instance_id
            agent.settings = settings
            
            allowed = agent.allowed_worker_types or []
            if "openclaw" not in allowed:
                allowed.append("openclaw")
            agent.allowed_worker_types = allowed
            
            db.commit()
            print(f"Agent {agent_id} successfully updated with instance {instance_id}.")
        else:
            print(f"Agent {agent_id} STILL NOT FOUND. Listing all IDs:")
            agents = db.query(Agent).all()
            for a in agents:
                print(f"- {a.id}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(update_agent())
