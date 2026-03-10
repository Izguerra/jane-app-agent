
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.tools.worker_tools import WorkerTools
from backend.database import SessionLocal

async def test_real_weather_execution():
    print("--- TESTING REAL WEATHER WORKER EXECUTION ---")
    
    # Initialize Tools
    # We need a valid workspace_id from the cleanup output or a dummy one
    # wrk_000V7dMzXJLzP5mYgdf7FzjA3J was in the cleanup logs
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" 
    # Fetch a valid Agent ID
    db = SessionLocal()
    try:
        from backend.models_db import Agent
        agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
        if not agent:
            print("❌ No agent found in workspace. Cannot run test.")
            return
        agent_id = agent.id
        print(f"Using Agent ID: {agent_id}")
    finally:
        db.close()

    tools = WorkerTools(workspace_id=workspace_id, agent_id=agent_id, allowed_worker_types=["weather-worker"])
    
    params = {"location": "Toronto, Ontario"}
    
    print(f"Dispatching run_task_now with params: {params}")
    
    try:
        # This calls:
        # 1. create_task (DB)
        # 2. get_worker_handler -> WeatherWorker._execute_logic
        # 3. loop.run_in_executor -> thread
        # 4. inside thread -> WeatherWorker calls asyncio.run(ExternalTools.get_weather)
        
        result = await asyncio.wait_for(tools.run_task_now("weather-worker", params), timeout=30.0)
        
        print("\n✅ RESULT RECEIVED:")
        print(result)
        
        if "Toronto" in result or "clouds" in result or "sunny" in result or "weather" in result.lower():
            print("✅ Output looks valid.")
        else:
            print("⚠️ Output might be error/unexpected.")
            
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT: Worker failed to return within 30s.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_weather_execution())
