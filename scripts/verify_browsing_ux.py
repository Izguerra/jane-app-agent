import asyncio
import sys
import os
import json

# Add parent directory to path to import backend
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.agent_tools import AgentTools

async def main():
    db = SessionLocal()
    try:
        workspace_id = "wrk__000V7dCbbMJVHLzTWb9HFWlNzR"
        agent_id = "agnt_000V9MA8opL0QNND3iH0CewpK0" # From screenshot
        
        tools = AgentTools(workspace_id=workspace_id, agent_id=agent_id)
        
        print("Testing Synchronous Browsing UX...")
        # This will call our newly sync-wrapped dispatch_to_openclaw
        result = await tools.dispatch_to_openclaw(
            task_description="Explain what Google is",
            start_url="https://www.google.com"
        )
        
        print(f"\nResult Received:\n{result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
