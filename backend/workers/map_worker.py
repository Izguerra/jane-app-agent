from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker
from backend.services.worker_service import WorkerService
from backend.tools.external_tools import ExternalTools
import asyncio

class MapWorker(BaseEnterpriseWorker):
    """
    Worker for navigation and traffic checks using Google Maps.
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
        
        origin = input_data.get("origin")
        destination = input_data.get("destination")
        travel_mode = input_data.get("travel_mode") or input_data.get("mode")
        
        if not origin or not destination:
            return {"error": "Origin and Destination are required"}
            
        if not travel_mode:
            return {"error": "Travel Mode is required (driving, walking, bicycling, transit)"}

        service.update_task_status(task_id, status="running", current_step=f"Calculating route from {origin} to {destination} ({travel_mode})...")
        
        tools = ExternalTools()
        
        try:
             result = asyncio.run(tools.get_directions(origin, destination, mode=travel_mode))
             return {"route_info": result}
        except Exception as e:
             return {"error": f"Failed to get directions: {str(e)}"}
