
import asyncio
import os
import sys
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agent_tools import AgentTools
from backend.database import SessionLocal
from backend.services.worker_service import WorkerService

# Mock LLM and Agent Context
class MockAgentTools(AgentTools):
    def __init__(self):
        self.workspace_id = "test_workspace_123"
        self.agent_id = "test_agent_123"
        self.customer_id = "test_customer_123"

async def test_sync_tools():
    print("=== Starting Comprehensive Sync Tool Verification ===\n")
    
    tools = MockAgentTools()
    
    # 1. Test Weather (Utility)
    print("1. Testing Weather Worker (Sync)...")
    try:
        # Note: This might hit real ExternalTools if keys are set, or fail if not.
        # We rely on the tool returning *something* other than "dispatched"
        result = await tools.run_task_now("weather-worker", json.dumps({"location": "Milton"}))
        print(f"   Result: {result}")
        if "weather" in result.lower() or "completed" in result.lower() or "Temp" in result:
             print("   [PASS] Weather execute_worker_sync returned data.")
        else:
             print("   [WARN] Weather output unexpected (check logs).")
    except Exception as e:
        print(f"   [FAIL] Weather Error: {e}")

    print("\n------------------------------------------------\n")

    # 2. Test Job Search (General Worker)
    print("2. Testing Job Search Worker (Sync)...")
    try:
        # Simulate Prompt having collected these slots
        params = {
            "job_title": "Product Manager",
            "location": "Remote",
            "job_type": "full-time"
        }
        result = await tools.run_task_now("job-search", json.dumps(params))
        print(f"   Result type: {type(result)}")
        print(f"   Result snippet: {str(result)[:200]}...")
        
        if "Found" in str(result) or "jobs" in str(result).lower():
            print("   [PASS] Job Search returned immediate results.")
        else:
             print("   [WARN] Job Search output unexpected.")
    except Exception as e:
        print(f"   [FAIL] Job Search Error: {e}")

    print("\n------------------------------------------------\n")
    
    # 3. Test Flight Tracker (Utility)
    print("3. Testing Flight Tracker (Sync)...")
    try:
        # Using a dummy flight or route
        params = {
            "flight_number": "AC415"
        }
        result = await tools.run_task_now("flight-tracker", json.dumps(params))
        print(f"   Result: {str(result)[:200]}...")
        if "Flight" in str(result) or "status" in str(result).lower():
             print("   [PASS] Flight Tracker returned data.")
        else:
             print("   [WARN] Flight Tracker output unexpected.")
    except Exception as e:
        print(f"   [FAIL] Flight Tracker Error: {e}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(test_sync_tools())
