import asyncio
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.services.worker_provisioner import WorkerProvisioner

async def main():
    db = SessionLocal()
    try:
        workspace_id = "wrk__000V7dCbbMJVHLzTWb9HFWlNzR"
        provisioner = WorkerProvisioner(db)
        
        print(f"Provisioning new OpenClaw instance for {workspace_id}...")
        instance = await provisioner.provision_instance(
            workspace_id=workspace_id,
            worker_type="openclaw",
            name="OpenClaw Verified Worker",
            llm_model="claude-3-5-sonnet"
        )
        print(f"Success! Instance ID: {instance.id}")
        print(f"Connection URL: {instance.connection_url}")
        print(f"Container ID: {instance.container_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
