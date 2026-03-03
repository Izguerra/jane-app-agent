import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import uuid

# Include the project root in sys.path to allow imports
import sys
sys.path.append(os.getcwd())

from backend.database import SessionLocal, engine
from backend.services.worker_provisioner import WorkerProvisioner
from backend.models_db import Agent

async def provision_and_update():
    db = SessionLocal()
    provisioner = WorkerProvisioner(db)
    
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    # CORRECTED ID with lowercase 'oo'
    agent_id = "agnt_000VA6fCM7ooHx7VALTwm40ed8"
    
    print(f"Provisioning new OpenClaw worker for workspace {workspace_id}...")
    try:
        # Provision a new instance
        llm_api_key = os.getenv("OPENROUTER_API_KEY") 
        
        instance = await provisioner.provision_instance(
            workspace_id=workspace_id,
            worker_type="openclaw",
            name="E2E OpenClaw Worker",
            llm_model="anthropic/claude-3.5-sonnet",
            llm_api_key=llm_api_key
        )
        
        print(f"Instance provisioned: {instance.id} at {instance.connection_url}")
        
        # List all agents in workspace to be sure
        agents = db.query(Agent).filter(Agent.workspace_id == workspace_id).all()
        print(f"Found {len(agents)} agents in workspace {workspace_id}:")
        for a in agents:
            print(f"- {a.name} ({a.id})")
            
        # Update specific agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            settings = agent.settings or {}
            settings["open_claw_instance_id"] = instance.id
            agent.settings = settings
            
            allowed = agent.allowed_worker_types or []
            if "openclaw" not in allowed:
                allowed.append("openclaw")
            agent.allowed_worker_types = allowed
            
            db.commit()
            print(f"Agent {agent_id} updated with new instance_id.")
        else:
            print(f"Agent {agent_id} NOT FOUND directly.")
            
    except Exception as e:
        print(f"Error during provisioning: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(provision_and_update())
