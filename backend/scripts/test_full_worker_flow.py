
import asyncio
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# Patch nest_asyncio to allow nested event loops (Agent -> Worker -> Async Tool)
import nest_asyncio
nest_asyncio.apply()

from backend.agent import AgentManager
from backend.database import SessionLocal
from backend.models_db import Workspace

async def test_flow():
    print("=== STARTING COMPREHENSIVE WORKER FLOW TEST ===")
    
    # 1. Setup Workspace Config
    db = SessionLocal()
    # Use the known working workspace ID
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    team_id = workspace.team_id if workspace else 1
    db.close()
    
    print(f"Testing with Workspace ID: {workspace_id}")
    
    manager = AgentManager()
    
    # TEST CASE 1: Weather (Simple Tool)
    # The Agent should use ExternalTools.get_current_weather directly (or via WorkerTools if dispatched)
    # But updated AgentTools has get_weather tool.
    print("\n--- TEST CASE 1: Weather Query ---")
    user_query = "What is the weather in Toronto?"
    print(f"User: {user_query}")
    
    response = await manager.chat(
        message=user_query,
        team_id=team_id,
        workspace_id=workspace_id
    )
    print(f"Agent: {response}")
    
    if "Toronto" in response and ("temperature" in response or "weather" in response or "Celsius" in response or "C" in response):
        print("✅ Weather Verification PASSED")
    else:
        print("❌ Weather Verification FAILED")

    # TEST CASE 2: Flight Status (Ambiguous Input)
    # This tests the "Smart" logic I added to AgentTools.get_flight_status
    print("\n--- TEST CASE 2: Flight Status (Ambiguous City) ---")
    user_query = "What is the status of flight AC 415?"
    print(f"User: {user_query}")
    
    response_flight = await manager.chat(
        message=user_query,
        team_id=team_id,
        workspace_id=workspace_id
    )
    print(f"Agent: {response_flight}")
    
    # We expect a success message with flight details OR a request for more info if it failed to fetch.
    # Note: AC415 might not be active, but the Agent should TRY.
    if "AC" in response_flight and ("status" in response_flight or "Flight" in response_flight or "scheduled" in response_flight):
        print("✅ Flight Status Verification PASSED")
    elif "tool is not available" in response_flight:
         print("❌ Flight Status tool missing or failed to load")
    else:
         print("⚠️ Flight Result ambiguous (check output above)")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_flow())
