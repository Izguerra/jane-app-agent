
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import WorkerTask, Workspace
from backend.routers.settings import get_settings

def debug_tasks():
    db = SessionLocal()
    try:
        print("--- Debugging Tasks ---")
        
        # 1. List Workspaces to find ID
        workspaces = db.query(Workspace).all()
        for w in workspaces:
            print(f"Workspace: {w.name} (ID: {w.id})")
            
            # 2. Check Settings for this workspace's Agent
            from backend.models_db import Agent
            agent = db.query(Agent).filter(Agent.workspace_id == w.id).first()
            if agent:
                print(f"  Agent Name: {agent.name}")
                print(f"  Agent Allowed Workers: {agent.allowed_worker_types}")
            else:
                print("  No Agent found for workspace.")

            # 3. List recent tasks
            tasks = db.query(WorkerTask).filter(WorkerTask.workspace_id == w.id).order_by(WorkerTask.created_at.desc()).limit(10).all()
            print(f"  Recent Tasks ({len(tasks)}):")
            for t in tasks:
                print(f"    - [{t.created_at}] {t.worker_type}: {t.status} (ID: {t.id})")
                if t.worker_type == 'email-worker' or t.worker_type == 'sms-messaging':
                    print(f"      Output: {str(t.output_data)[:100]}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_tasks()
