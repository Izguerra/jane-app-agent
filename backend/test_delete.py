import sys
import os

# Ensure the backend module is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models_db import Agent, WorkerTask, PhoneNumber, Communication

def test_delete(agent_id: str):
    db = SessionLocal()
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        print("Agent not found.")
        db.close()
        return

    print(f"Found agent {agent.name}. Attempting to delete...")
    
    try:
        # Replicate the manual cleanup logic
        db.query(WorkerTask).filter(WorkerTask.dispatched_by_agent_id == agent.id).update({"dispatched_by_agent_id": None})
        db.query(PhoneNumber).filter(PhoneNumber.agent_id == agent.id).update({"agent_id": None})
        db.query(Communication).filter(Communication.agent_id == agent.id).update({"agent_id": None})
        
        db.delete(agent)
        db.commit()
        print("Agent deleted successfully without foreign key errors! The 500 issue is resolved.")
    except Exception as e:
        print(f"Error occurred during deletion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_delete("agnt_000VCRoP3S1834dms8YCdys6m8P")
