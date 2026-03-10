import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.tools.worker_tools import WorkerTools
from backend.database import SessionLocal

async def run_tests():
    print("=== STARTING WORKER ECOSYSTEM 2.0 COMPREHENSIVE TEST ===\n")
    
    # Mock context
    # Real Workspace ID from DB check
    REAL_WORKSPACE_ID = "wrk__000V7dCbbMJVHLzTWb9HFWlNzR"
    REAL_AGENT_ID = "agnt_000V9MA8opL0QNND3iH0CewpK0" 
    tools = WorkerTools(workspace_id=REAL_WORKSPACE_ID, agent_id=REAL_AGENT_ID)
    # We need to ensure we can actually run these (permissions usually checked in Agent, but tools check 'allowed_worker_types' if set)
    # By default allowed_worker_types is None in init so it allows all, ensuring we can test.

    results = []

    async def test_case(name, coroutine, expected_substring=None, should_fail=False):
        print(f"TEST: {name}...")
        try:
            result = await coroutine
            result_str = str(result)
            
            if should_fail:
                # We expect an error message
                if "Error" in result_str or "Missing" in result_str:
                     print(f"✅ PASS: Correctly blocked/failed as expected. Output: {result_str[:100]}...")
                     results.append((name, "PASS"))
                else:
                     print(f"❌ FAIL: Expected failure but got success. Output: {result_str[:100]}...")
                     results.append((name, "FAIL"))
            else:
                # We expect success
                if "Error" in result_str and "Missing" not in result_str: # Allow "No flights found" acting as success of logic
                     # Simple heuristics
                     if expected_substring and expected_substring not in result_str:
                         print(f"❌ FAIL: Missing expected content '{expected_substring}'. Output: {result_str[:100]}...")
                         results.append((name, "FAIL"))
                     else:
                         print(f"❌ FAIL: Returned Error. Output: {result_str[:100]}...")
                         results.append((name, "FAIL"))
                else:
                     if expected_substring and expected_substring not in result_str:
                         print(f"❌ FAIL: Missing expected content '{expected_substring}'. Output: {result_str[:100]}...")
                         results.append((name, "FAIL"))
                     else:
                         print(f"✅ PASS. Output: {result_str[:100]}...")
                         results.append((name, "PASS"))
                         
        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e}")
            results.append((name, "ERROR"))
        print("-" * 40)

    # 1. Validation Logic ("The Police")
    await test_case(
        "Validation: SMS Missing Message", 
        tools.run_task_now("sms-messaging", {"recipient_number": "555-1234"}),
        should_fail=True # Expect strict "Missing Parameter" error
    )
    
    await test_case(
        "Validation: Flight Missing All", 
        tools.run_task_now("flight-tracker", {}),
        should_fail=True
    )

    # 2. Feature: Weather Forecast (Mocked via logic, requires API key)
    # We use a specific date format because the Agent usually resolves "tomorrow" to YYYY-MM-DD.
    # Worker logic does simple string matching.
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    await test_case(
        f"Feature: Weather Forecast ({tomorrow}, Imperial)",
        tools.run_task_now("weather-worker", {"location": "New York", "date": tomorrow, "units": "imperial", "details": ["humidity"]}),
        expected_substring="Temp" # Basic check if it returns a weather report
    )

    # 3. Feature: Flight Schedule 
    await test_case(
        "Feature: Flight Schedule (YYZ->YUL approx 5pm)",
        tools.run_task_now("flight-tracker", {"origin": "YYZ", "destination": "YUL", "approx_time": "5pm"}),
        expected_substring="✈️" # Check for the emoji used in new formatter
    )
    
    # 4. Feature: Job Search Filters
    await test_case(
        "Feature: Job Search (Senior, Remote)",
        tools.run_task_now("job-search", {"job_title": "Python Developer", "level": "Senior", "location_type": "Remote", "job_type": "Full-time"}),
        expected_substring="Found" or "No jobs"
    )

    print("\n=== TEST SUMMARY ===")
    for name, status in results:
        print(f"{status}: {name}")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(run_tests())
