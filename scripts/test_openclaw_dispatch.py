
import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

from backend.database import SessionLocal
from backend.services.worker_service import WorkerService
from backend.models_db import Agent, WorkerInstance

async def test_dispatch():
    print("=== OpenClaw E2E Dispatch Test ===")
    
    # 1. Setup Context
    agent_id = "agnt_000V9MA8opL0QNND3iH0CewpK0" # From user's logs
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" # From previous steps
    
    db = SessionLocal()
    try:
        # 2. Get Agent & Validate Configuration
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            print(f"FAILED: Agent {agent_id} not found.")
            return

        print(f"Agent: {agent.name}")
        print(f"Allowed Workers: {agent.allowed_worker_types}")
        
        if "openclaw" not in (agent.allowed_worker_types or []):
            print("FAILED: 'openclaw' not in allowed_worker_types!")
            return

        settings = agent.settings or {}
        instance_id = settings.get("openClawInstanceId") or settings.get("open_claw_instance_id")
        print(f"Configured Instance ID: {instance_id}")

        if not instance_id:
            print("FAILED: No openClawInstanceId in agent settings.")
            return

        # 3. Validate Instance Exists
        instance = db.query(WorkerInstance).filter(WorkerInstance.id == instance_id).first()
        if not instance:
            print(f"FAILED: Instance {instance_id} not found in DB.")
            return
        print(f"Instance Found: {instance.name} (Status: {instance.status})")

        # 4. Simulate Dispatch (Direct Service Call)
        print("\n--- Attempting Dispatch via WorkerService ---")
        service = WorkerService(db)
        
        try:
            task = service.create_task(
                workspace_id=workspace_id,
                worker_type="openclaw",
                input_data={
                    "goal": "E2E Test: Browse example.com", 
                    "url": "https://example.com", 
                    "instance_id": instance_id
                },
                dispatched_by_agent_id=agent_id
            )
            print(f"SUCCESS: Task Created!")
            print(f"Task ID: {task.id}")
            print(f"Status: {task.status}")
            print(f"Worker Type: {task.worker_type}")
            
        except Exception as e:
            print(f"FAILED: Dispatch error: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_dispatch())
