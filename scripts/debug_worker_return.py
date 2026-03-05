
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.tools.worker_tools import WorkerTools

async def test_worker_return():
    print("--- TESTING WorkerTools.run_task_now RETURN VALUE ---")
    
    # Mock parameters
    workspace_id = "wrk__000V7dCbbMJVHLzTWb9HFWlNzR" 
    # Use WorkerTools directly, authorized for all
    tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=["weather-worker", "job-search"])
    
    # Test 1: Weather (Simple Utility)
    print("\n1. Testing 'weather-worker'...")
    try:
        # Note: Input parameters are dict for WorkerTools (unlike AgentTools which took string)
        # Checking implementation... yes, parameter: dict
        result = await tools.run_task_now("weather-worker", {"location": "New York"})
        print(f"RESULT TYPE: {type(result)}")
        print(f"RESULT VALUE: {result}")
        
        if not result or result == "None":
            print("[FAIL] Weather returned empty/None")
        else:
            print("[PASS] Weather returned data")
            
    except Exception as e:
        print(f"[ERROR] Weather test failed: {e}")

    # Test 2: Job Search (Complex Worker)
    print("\n2. Testing 'job-search'...")
    try:
        result = await tools.run_task_now("job-search", {"job_title": "Test Engineer", "location": "Remote"})
        print(f"RESULT TYPE: {type(result)}")
        print(f"RESULT VALUE: {result[:200]}...") # Truncate
        
        if not result or result == "None":
             print("[FAIL] Job Search returned empty/None")
        else:
             print("[PASS] Job Search returned data")
             
    except Exception as e:
        print(f"[ERROR] Job Search test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_worker_return())
