from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker
from backend.services.worker_service import WorkerService
from backend.tools.external_tools import ExternalTools
import asyncio

class FlightTrackerWorker(BaseEnterpriseWorker):
    """
    Worker for tracking flight status.
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
        
        flight_number = input_data.get("flight_number")
        origin = input_data.get("origin")
        destination = input_data.get("destination")
        airline = input_data.get("airline")
        date_query = input_data.get("date")
        approx_time = input_data.get("approx_time")

        if not flight_number and not (origin and destination):
             return {"error": "Either Flight Number OR Origin/Destination is required."}

        # Define async resolution logic
        async def resolve_and_fetch():
            nonlocal origin, destination
            
            # Batch Resolution Step
            cities_to_resolve = []
            if origin and len(origin) > 3: cities_to_resolve.append(("origin", origin))
            if destination and len(destination) > 3: cities_to_resolve.append(("destination", destination))
            
            if cities_to_resolve:
                service.update_task_status(task_id, status="running", current_step=f"Resolving airport codes for {', '.join([c[1] for c in cities_to_resolve])}...", steps_completed=1, steps_total=5)
                resolutions = await cls._batch_resolve_iata([c[1] for c in cities_to_resolve])
                
                for idx, (type, name) in enumerate(cities_to_resolve):
                    res = resolutions.get(name, [])
                    if len(res) > 1:
                        return {"error": f"Multiple airports found for {name}: {', '.join(res)}. Please specify."}
                    elif len(res) == 1:
                        if type == "origin": origin = res[0]
                        else: destination = res[0]
                    else:
                        # Fallback to original name if not found
                        pass

            service.update_task_status(task_id, status="running", current_step="Checking flight status (External Tool)...", steps_completed=2, steps_total=5)
            
            tools = ExternalTools()
            try:
                 return {"flight_status": await asyncio.wait_for(
                     tools.get_flight_status(
                        flight_number=flight_number, 
                        origin=origin, 
                        destination=destination, 
                        airline=airline,
                        date=date_query,
                        approx_time=approx_time
                     ),
                     timeout=15.0
                 )}
            except Exception as e:
                 return {"error": f"Failed to track flight: {str(e)}"}

        # Execute async logic synchronously
        # Since we are running in a thread (via WorkerTools.run_task_now -> run_in_executor),
        # we do not have a running event loop in this thread.
        # We can safely use asyncio.run() to create a temporary loop for the async ExternalTools.
        try:
             import asyncio
             # Use nest_asyncio just in case
             import nest_asyncio
             nest_asyncio.apply()
             return asyncio.run(resolve_and_fetch())
        except Exception as e:
             return {"error": f"Resolution/Execution Error: {str(e)}"}

    @staticmethod
    async def _batch_resolve_iata(city_names: List[str]) -> Dict[str, List[str]]:
        """
        Batch resolve city names to IATA codes using a single LLM call.
        """
        if not city_names:
            return {}

        try:
            from backend.lib.ai_client import get_ai_client
            client, model_name = get_ai_client(async_mode=True)
            
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Return a JSON object where keys are the input city names/airport names and values are lists of major IATA airport codes. Example: {'London': ['LHR', 'LGW'], 'Heathrow': ['LHR']}"},
                    {"role": "user", "content": f"Resolve these: {', '.join(city_names)}"}
                ],
                response_format={ "type": "json_object" }
            )
            
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"IATA Batch Resolution Error: {e}")
            return {name: [name] for name in city_names}

    @staticmethod
    async def _resolve_iata(city_name: str) -> List[str]:
        # Deprecated: usage should move to _batch_resolve_iata
        res = await FlightTrackerWorker._batch_resolve_iata([city_name])
        return res.get(city_name, [city_name])
