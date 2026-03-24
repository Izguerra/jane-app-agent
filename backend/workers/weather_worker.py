from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker
from backend.services.worker_service import WorkerService
from backend.tools.external_tools import ExternalTools

class WeatherWorker(BaseEnterpriseWorker):
    """
    Worker for checking weather conditions.
    """
    RISK_LEVEL = "low"

    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        # Robust extraction of location
        location = input_data.get("location") or input_data.get("address") or input_data.get("city")
        
        # Fallback: Extract from description if available
        if not location and input_data.get("description"):
            desc = input_data.get("description").lower()
            # Simple heuristic: "weather in [City]"
            if "weather in " in desc:
                parts = desc.split("weather in ")
                if len(parts) > 1:
                    location = parts[1].split(" ")[0].strip("?.!,") # Take first word/token as city roughly
            elif "weather for " in desc:
                 parts = desc.split("weather for ")
                 if len(parts) > 1:
                    location = parts[1].split(" ")[0].strip("?.!,")

        if not location:
            return {"error": "Location is required. Please specify a city or region."}
            
        date_query = input_data.get("date")
        units = input_data.get("units", "metric")
        details = input_data.get("details", []) # List of detailed metrics requested

        # Log step
        service.update_task_status(task_id, status="running", current_step=f"Fetching weather for {location}...")
        
        # Use the workspace_id if available in input_data or elsewhere
        workspace_id = input_data.get("workspace_id")
        tools = ExternalTools(workspace_id=workspace_id)
        
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        print(f"DEBUG: WeatherWorker executing for {location}")
        try:
             # Since we are running in a thread (via WorkerTools.run_task_now -> run_in_executor),
             # we do not have a running event loop in this thread.
             # We can safely use asyncio.run() to create a temporary loop for the async ExternalTools.
             result = asyncio.run(tools.get_current_weather(location, date=date_query, units=units, details=details))
             print(f"DEBUG: WeatherWorker result: {result}")
             return {"weather_info": result}
        except Exception as e:
             print(f"DEBUG: WeatherWorker ERROR: {e}")
             return {"error": f"Could not execute weather fetch: {str(e)}"}
