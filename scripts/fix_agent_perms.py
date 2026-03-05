from backend.database import SessionLocal
from backend.models_db import Agent, Workspace
import json

def update_agent_permissions():
    db = SessionLocal()
    try:
        # User's workspace from screenshot
        workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" 
        
        print(f"Checking workspace {workspace_id}...")
        
        agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
        if not agent:
            print("No agent found for this workspace.")
            return

        print(f"Found Agent: {agent.name} (ID: {agent.id})")
        
        current_workers = agent.allowed_worker_types or []
        # Ensure it's a list (it might be None or JSON string if not parsed by model, but SQLAlchemy handles JSON type)
        if isinstance(current_workers, str):
            current_workers = json.loads(current_workers)
            
        print(f"Current allowed workers: {current_workers}")
        
        needed = ["sms-messaging", "email-worker"]
        changed = False
        
        for n in needed:
            if n not in current_workers:
                current_workers.append(n)
                changed = True
                print(f"Adding {n}...")
        
        if changed:
            agent.allowed_worker_types = current_workers
            db.commit()
            print(f"Updated allowed_worker_types to: {current_workers}")
        else:
            print("Permissions already correct.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_agent_permissions()
