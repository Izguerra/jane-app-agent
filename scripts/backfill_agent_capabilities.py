
import os
import sys
import json
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Agent, Workspace

REQUIRED_WORKERS = ["weather-worker", "flight-tracker", "lead-research", "content-writer", "web-research"]

def backfill():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        print(f"Found {len(agents)} agents to verify.")
        
        for agent in agents:
            # Update the direct column
            current_workers = agent.allowed_worker_types or []
            if not isinstance(current_workers, list):
                current_workers = []
            
            missing = [w for w in REQUIRED_WORKERS if w not in current_workers]
            if missing:
                print(f"Agent '{agent.name}' ({agent.id}) missing: {missing}. Adding...")
                agent.allowed_worker_types = list(set(current_workers + REQUIRED_WORKERS))
                db.add(agent)
            
            # Sync to settings JSON just in case any legacy code still looks there
            if not agent.settings:
                agent.settings = {}
            
            # Ensure settings is a copy to trigger SQLAlchemy change detection
            s = dict(agent.settings)
            s["allowed_worker_types"] = agent.allowed_worker_types
            agent.settings = s
            db.add(agent)
            
        db.commit()
        print("✅ Backfill complete.")
    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
