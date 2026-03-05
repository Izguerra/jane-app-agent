
import asyncio
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()
import nest_asyncio
nest_asyncio.apply()

from backend.database import SessionLocal
from backend.services.worker_service import WorkerService

def test_weather_fallback():
    print("=== TESTING WEATHER WORKER ROBUSTNESS ===")
    
    db = SessionLocal()
    service = WorkerService(db)
    
    # Simulate the "bad" LLM call: Missing 'location', but has 'description'
    input_data = {
        "description": "Check the weather in Vancouver please",
        # "location": "Vancouver"  <-- MISSING
    }
    
    print(f"DTO Input: {input_data}")
    
    # Create task
    task = service.create_task(
        workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J", # Known ID
        worker_type="weather-worker",
        input_data=input_data
    )
    
    print(f"Task created: {task.id}")
    
    # Execute manually (simulate run_task_now)
    from backend.workers.weather_worker import WeatherWorker
    
    result = WeatherWorker._execute_logic(task.id, input_data, service, db)
    
    print(f"Result: {result}")
    
    if "weather_info" in result and "Vancouver" in str(result["weather_info"]):
        print("✅ SUCCESS: Extracted 'Vancouver' from description")
    elif "error" in result:
        print(f"❌ FAILED: {result['error']}")
    else:
        print("⚠️ UNKNOWN RESULT")
        
    db.close()

if __name__ == "__main__":
    test_weather_fallback()
