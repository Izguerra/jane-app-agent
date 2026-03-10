
import sys
import os
import time
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.tools.worker_tools import WorkerTools
# We need to patch where ExternalTools is used, which is inside the specific workers.
# But ExternalTools calls aiohttp, so let's patch ExternalTools methods directly to keep it simple and robust?
# Or patch aiohttp.
# Patching ExternalTools methods is easier and less brittle to URL changes.

async def verify_scenarios():
    print("--- Starting Scenario Verification ---")
    
    # Initialize Tools
    tools = WorkerTools(workspace_id=1, agent_id=1)
    tools.allowed_worker_types = ["weather-worker", "flight-tracker-worker", "map-worker"]

    # 1. Weather Scenario
    print("\n[Scenario 1] User: 'What is the temperature in Springfield?'")
    print("Action: run_task_now('weather-worker', {'location': 'Springfield'})")
    
    start_time = time.time()
    
    # Mock WorkerService and DB to avoid DB interaction
    with patch('backend.database.SessionLocal') as MockDB:
        MockDB.return_value = MagicMock()
        with patch('backend.services.worker_service.WorkerService') as MockServiceClass:
            mock_service = MockServiceClass.return_value
            mock_service.create_task.return_value = MagicMock(id="weather-task-1")
            
            # Mock ExternalTools.get_current_weather
            # Note: workers instantiate ExternalTools inside _execute_logic usually.
            # We need to verify where ExternalTools is imported in weather_worker.py 
            # It is: from backend.tools.external_tools import ExternalTools
            
            with patch('backend.workers.weather_worker.ExternalTools') as MockExternalTools:
                mock_tool_instance = MockExternalTools.return_value
                # It returns a coroutine
                mock_tool_instance.get_current_weather = AsyncMock(return_value="The weather in Springfield is currently clear sky with a temperature of 22°C and 45% humidity.")
                
                result = await tools.run_task_now("weather-worker", {"location": "Springfield"})
                
                duration = time.time() - start_time
                print(f"Time: {duration:.4f}s")
                print(f"Result: {result}")
                
                if "22°C" in str(result):
                    print("PASS: Weather result correct.")
                else:
                    print("FAIL: Weather result mismatch.")

    # 2. Flight Scenario
    print("\n[Scenario 2] User: 'What is the status of flight AC 415?'")
    print("Action: run_task_now('flight-tracker-worker', {'flight_number': 'AC 415'})")
    
    start_time = time.time()
    
    with patch('backend.database.SessionLocal') as MockDB:
        MockDB.return_value = MagicMock()
        with patch('backend.services.worker_service.WorkerService') as MockServiceClass:
            mock_service = MockServiceClass.return_value
            mock_service.create_task.return_value = MagicMock(id="flight-task-1")
            
            with patch('backend.workers.flight_tracker_worker.ExternalTools') as MockExternalTools:
                mock_tool_instance = MockExternalTools.return_value
                
                flight_response = "• Flight AC415 (Air Canada): active. YYZ -> YUL. Departs: 2023-10-27T10:00:00"
                mock_tool_instance.get_flight_status = AsyncMock(return_value=flight_response)
                
                result = await tools.run_task_now("flight-tracker-worker", {"flight_number": "AC 415"})
                
                duration = time.time() - start_time
                print(f"Time: {duration:.4f}s")
                print(f"Result: {result}")
                
                if "AC415" in str(result):
                    print("PASS: Flight result correct.")
                else:
                    print("FAIL: Flight result mismatch.")

    # 3. Map Scenario (Missing Origin)
    print("\n[Scenario 3] User: 'How long does it take to get to CN Tower?'")
    print("Action: run_task_now('map-worker', {'destination': 'CN Tower'}) (Missing Origin)")
    
    with patch('backend.database.SessionLocal') as MockDB:
        MockDB.return_value = MagicMock()
        with patch('backend.services.worker_service.WorkerService') as MockServiceClass:
            # We don't need to patch ExternalTools here because it should fail BEFORE calling tools
            
            result = await tools.run_task_now("map-worker", {"destination": "CN Tower"})
            print(f"Result: {result}")
            
            if "Origin and Destination are required" in str(result):
                print("PASS: Worker correctly rejected missing origin.")
            else:
                print(f"FAIL: Worker should have rejected it. Got: {result}")

    # 4. Map Scenario (Missing Travel Mode)
    print("\n[Scenario 4] User: 'How long to CN Tower from Springfield?'")
    print("Action: run_task_now('map-worker', {'origin': 'Springfield', 'destination': 'CN Tower'}) (Missing Mode)")
    
    with patch('backend.database.SessionLocal') as MockDB:
        MockDB.return_value = MagicMock()
        with patch('backend.services.worker_service.WorkerService') as MockServiceClass:
            result = await tools.run_task_now("map-worker", {"origin": "Springfield", "destination": "CN Tower"})
            print(f"Result: {result}")
            
            if "Travel Mode is required" in str(result):
                print("PASS: Worker correctly rejected missing travel_mode.")
            else:
                print(f"FAIL: Worker should have rejected it. Got: {result}")

    # 5. Map Scenario (Success)
    print("\n[Scenario 5] User: 'Walking to CN Tower from Springfield'")
    print("Action: run_task_now('map-worker', {'origin': 'Springfield', 'destination': 'CN Tower', 'travel_mode': 'walking'})")
    
    with patch('backend.database.SessionLocal') as MockDB:
        MockDB.return_value = MagicMock()
        with patch('backend.services.worker_service.WorkerService') as MockServiceClass:
            mock_service = MockServiceClass.return_value
            mock_service.create_task.return_value = MagicMock(id="map-task-1")
            
            with patch('backend.workers.map_worker.ExternalTools') as MockExternalTools:
                mock_tool_instance = MockExternalTools.return_value
                mock_tool_instance.get_directions = AsyncMock(return_value="The walking directions from Springfield to CN Tower is 10km and takes 2 hours.")
                
                result = await tools.run_task_now("map-worker", {"origin": "Springfield", "destination": "CN Tower", "travel_mode": "walking"})
                print(f"Result: {result}")
                
                if "walking directions" in str(result):
                    print("PASS: Map result correct.")
                else:
                    print("FAIL: Map result mismatch.")

if __name__ == "__main__":
    asyncio.run(verify_scenarios())
