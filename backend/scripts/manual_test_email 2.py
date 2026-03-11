
import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.workers.email_worker import EmailWorker
from backend.services.worker_service import WorkerService

async def main():
    # Mock Service (We don't need real worker service logic for this test)
    mock_service = MagicMock(spec=WorkerService)
    
    # Mock Task object identifying the workspace
    # Mock Task object identifying the workspace
    mock_task = MagicMock()
    mock_task.workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" # Real Active Workspace
    mock_service.get_task.return_value = mock_task
    
    # Logging mocks
    mock_service.add_task_log = MagicMock(side_effect=lambda t, m, level="info": print(f"[LOG]: {m}"))
    mock_service.update_task_status = MagicMock(side_effect=lambda t, **kwargs: print(f"[STATUS]: {kwargs}"))

    input_data = {
        "action": "send",
        "recipient": "randyesguerra@hotmail.com",
        "cc": ["resguerra75@gmail.com"],
        "subject": "Test Email from JaneAppAgent",
        "body": "This is a manual test email sent by the EmailWorker to verify CC functionality."
    }
    
    print("Initializing EmailWorker...")
    # Ensure OPENAI_API_KEY is set (Worker checks it even for send action)
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set in env, worker might fail check.")
        # We might need to set a dummy one if we are purely sending, but the worker init checks it.
        # os.environ["OPENAI_API_KEY"] = "sk-dummy" 
    
    try:
        print(f"Sending email to {input_data['recipient']} (CC: {input_data['cc']})...")
        result = await EmailWorker._execute_async("test-task-id", input_data, mock_service)
        print("\n--- Execution Result ---")
        print(result)
    except Exception as e:
        print(f"\n[ERROR] Failed to execute worker: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
