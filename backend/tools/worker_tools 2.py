"""
Worker Tools

Tools for dispatching and managing autonomous worker tasks from within agent conversations.
Allows reactive agents (chat/voice) to trigger worker agents.
"""

from typing import Optional, Dict, Any, List
from backend.database import SessionLocal
from backend.services.worker_service import WorkerService
from livekit.agents import llm

class WorkerTools:
    def __init__(self, workspace_id: str, agent_id: Optional[str] = None, allowed_worker_types: Optional[List[str]] = None):
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        # Store allowed worker types for permission enforcement
        self.allowed_worker_types = allowed_worker_types or []
        self.session = None # Injected by Voice Agent
        print(f"DEBUG: WorkerTools initialized with allowed_worker_types: {self.allowed_worker_types}")

    async def _play_filler(self, message: str = "One moment please..."):
        """Plays a filler message to bridge latency for slow tools"""
        if hasattr(self, 'session') and self.session:
            try:
                # LiveKit API changes dynamically depending on SDK version, try both
                if hasattr(self.session, 'say'):
                    self.session.say(message, allow_interruptions=False, add_to_chat_ctx=False)
                    print(f"🔊 Playing filler audio: {message}")
            except Exception as e:
                print(f"🔊 Failed to play filler audio: {e}")

    # --- VALIDATION SCHEMAS (The Police) ---
    VALIDATION_SCHEMAS = {
        "sms-messaging": {
            "required": ["recipient_number", "message"],
            "error_msg": "Sending an SMS requires a 'recipient_number' AND a 'message'. Ask the user for the message content if missing."
        },
        "email-worker": {
            "required": [], 
            "notes": "Action 'send' requires: 'recipient', 'subject', 'body'. Action 'reply' and 'list' are generic."
        },
        "flight-tracker": {
            "required": [], 
            "error_msg": "Flight tracking requires either a 'flight_number' OR an 'origin' and 'destination'."
        },
        "map-worker": {
            "required": ["origin", "destination", "mode"],
            "error_msg": "Navigation requires 'origin', 'destination', and 'mode' (driving/transit/walking)."
        },
        "weather-worker": {
            "required": ["location"],
            "error_msg": "Weather checks require a 'location'."
        },
        "job-search": {
            "required": ["job_title", "location"],
            "error_msg": "Job Search requires: 'job_title' and 'location'. Optional: 'level', 'job_type'."
        },
        "sales-outreach": {
            "required": ["target_role", "company_list"],
            "error_msg": "Sales Outreach requires a 'target_role' and a 'company_list'."
        },
        "hr-onboarding": {
            "required": ["candidate_name"],
            "error_msg": "HR Onboarding requires a 'candidate_name'."
        },
        "intelligent-routing": {
            "required": ["text"],
            "error_msg": "Routing requires input 'text'."
        }
    }

    def _validate_response(self, worker_type: str, result: Any) -> Any:
        """
        Validate data RECEIVED from the worker.
        Ensures the worker managed to answer the user's request accurately.
        """
        # 1. Check for basic errors
        if isinstance(result, dict) and "error" in result:
            # Pass through the error, but log it clearly
            print(f"VALIDATION FAILED (Output) for {worker_type}: {result['error']}")
            return result
            
        # 2. Check for empty/useless results
        if not result:
            return {"error": f"Worker {worker_type} returned no data."}
            
        # 3. Type-specific checks (The Quality Control)
        if worker_type == "weather-worker" and isinstance(result, str):
            if "unknown" in result.lower() or "could not" in result.lower():
               # Attempt recovery or better error message?
               pass
               
        return result

    def _validate_params(self, worker_type: str, params: dict) -> Optional[str]:
        """
        Validate data BEFORE sending to worker.
        Returns error string if invalid, None if valid.
        """
        if not params:
            return f"Error: No parameters provided for {worker_type}."
            
        # 1. Generic Schema Check
        schema = self.VALIDATION_SCHEMAS.get(worker_type)
        if schema:
            for req in schema.get("required", []):
                if req not in params or not params[req]:
                    return f"Missing Parameter Error: {schema.get('error_msg')}"
                    
        # 2. Conditional / Complex Logic
        if worker_type == "email-worker":
            action = params.get("action", "list")
            if action == "send":
                if not params.get("recipient") or not params.get("body") or not params.get("subject"):
                    return "Email Sending Error: Requires 'recipient', 'subject', and 'body'. Ask the user for these details."
                    
        if worker_type == "flight-tracker":
            if not params.get("flight_number") and not (params.get("origin") and params.get("destination")):
                return self.VALIDATION_SCHEMAS["flight-tracker"]["error_msg"]
                
        return None

    @llm.function_tool(
        description="Dispatch a LONG-RUNNING background worker task (e.g., thorough research, report generation, mass emails). Do NOT use this for quick questions or interactive tasks. This returns a Task ID, not the result."
    )
    async def dispatch_worker_task(self, worker_type: str, parameters: dict) -> str:
        """
        Dispatch a background worker task for long-running operations.
        
        Use this ONLY when the user needs a task that takes time (minutes/hours),
        such as deep research, generating long content, or gathering extensive data.
        
        For immediate answers (weather, flights, quick search), usage `run_task_now` instead.
        
        Args:
            worker_type: The type of worker to dispatch.
            parameters: The parameters required by the worker. YOU MUST ASK the user for any missing required parameters defined in the worker schema BEFORE calling this.
            
        Returns:
            JSON string with task_id and status.
        """
        # PERMISSION CHECK: Verify this worker type is allowed for this agent
        if self.allowed_worker_types and worker_type not in self.allowed_worker_types:
            print(f"PERMISSION DENIED: Worker '{worker_type}' not in allowed list: {self.allowed_worker_types}")
            return f"Error: You are not authorized to use the '{worker_type}' worker. This capability is not enabled for this agent."
        
        # VALIDATION (The Police)
        error = self._validate_params(worker_type, parameters)
        if error:
            return error
        
        db = SessionLocal()
        try:
            service = WorkerService(db)
            
            # Verify worker exists and is active
            template = service.get_template_by_slug(worker_type)
            if not template or not template.is_active:
                return f"Error: Worker type '{worker_type}' is not available or inactive."

            # Create actual task
            task = service.create_task(
                workspace_id=self.workspace_id,
                worker_type=worker_type,
                input_data=parameters,
                dispatched_by_agent_id=self.agent_id
            )
            
            return f"Task dispatched successfully. Task ID: {task.id}. Status: {task.status}. usage: You can check status later using check_worker_status('{task.id}')."
        except Exception as e:
            return f"Error dispatching worker: {str(e)}"
        finally:
            db.close()


    async def get_worker_schema(self, worker_type: str) -> dict:
        """
        Get the parameter schema for a worker type.
        
        Call this before dispatch_worker_task to understand 
        what parameters are required.
        
        Args:
            worker_type: The worker type slug (e.g., "job-search")
            
        Returns:
            JSON Schema describing the parameters.
        """
        db = SessionLocal()
        try:
            service = WorkerService(db)
            schema = service.get_template_schema(worker_type)
            if schema:
                return schema
            return {"error": f"Unknown worker type: {worker_type}"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()


    @llm.function_tool(
        description="Check the status of a previously dispatched worker task."
    )
    async def check_worker_status(self, task_id: str) -> str:
        """
        Check the status of a previously dispatched worker task.
        
        Args:
            task_id: The task ID returned from dispatch_worker_task
            
        Returns:
            Status summary string.
        """
        db = SessionLocal()
        try:
            service = WorkerService(db)
            task = service.get_task(task_id)
            if task:
                if task.status == "completed":
                    import json
                    return f"Task ID: {task.id}\nStatus: {task.status}\nOutput: {json.dumps(task.output_data, indent=2)}"
                elif task.status == "failed":
                    return f"Task ID: {task.id}\nStatus: {task.status}\nError: {task.error_message}"
                else:
                    return f"Task ID: {task.id}\nStatus: {task.status}\nProgress: {task.steps_completed}/{task.steps_total or '?'}\nCurrent Step: {task.current_step}"
            return "Task not found."
        except Exception as e:
            return f"Error checking status: {str(e)}"
        finally:
            db.close()


    @llm.function_tool(
        description="List all available worker types that can be dispatched."
    )
    async def list_available_workers(self) -> str:
        """
        List all available worker types.
        
        Returns:
            List of available workers with descriptions.
        """
        db = SessionLocal()
        try:
            service = WorkerService(db)
            templates = service.get_all_templates(active_only=True)
            
            if not templates:
                return "No active workers available."
                
            result = "Available Workers:\n"
            for t in templates:
                result += f"- {t.name} (ID: {t.slug}): {t.description}\n"
            return result
        except Exception as e:
            return f"Error listing workers: {str(e)}"
        finally:
            db.close()
    @llm.function_tool(
        description="Schedule a worker task to run repeatedly. Use expressions like 'daily at 9am', 'hourly', or 'every Monday at 10:00'."
    )
    async def schedule_worker_task(self, worker_type: str, schedule_expression: str, parameters: dict) -> str:
        """
        Schedule a worker task to run repeatedly.
        
        Args:
            worker_type: The type of worker (e.g. "job-search").
            schedule_expression: When to run the task. 
                Examples: "daily at 9am", "every Monday at 14:00", "hourly", "every day at 5pm".
            parameters: The input parameters for the worker.
            
        Returns:
            Confirmation string with schedule ID.
        """
        db = SessionLocal()
        try:
            # Lazy import to avoid circular dependency if any
            from backend.services.scheduler_service import SchedulerService
            scheduler = SchedulerService(db)
            
            schedule = scheduler.create_schedule(
                workspace_id=self.workspace_id,
                worker_type=worker_type,
                schedule_expression=schedule_expression,
                input_data=parameters,
                user_id=None # Agent created
            )
            
            return f"Schedule created successfully. ID: {schedule.id}. First run scheduled for: {schedule.next_run_at}"
        except Exception as e:
            return f"Error scheduling task: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Execute a task IMMEDIATELY and return the result. Use this for ALL normal interactive requests (Weather, Flights, Job Search, Research, Email, etc.) where the user is waiting for an answer.",
    )
    async def run_task_now(self, worker_type: str, parameters: dict) -> str:
        """
        Execute a worker synchronously and get the result immediately.
        
        Use this for almost all user requests unless they explicitly ask for a background job
        or the task is obviously very long-running.
        
        Args:
            worker_type: The worker slug (e.g. 'job-search', 'weather-worker').
            parameters: The input parameters for the worker. YOU MUST ASK the user for any missing required parameters defined in the worker schema BEFORE calling this.
            
        Returns:
            The direct result from the worker.
        """
        # PERMISSION CHECK
        if self.allowed_worker_types and worker_type not in self.allowed_worker_types:
             return f"Error: You are not authorized to use the '{worker_type}' worker."

        # VALIDATION (The Police)
        error = self._validate_params(worker_type, parameters)
        if error:
            return error

        # Play filler audio if supported
        import random
        fillers = [
            "Let me look that up for you...",
            "Just a moment...",
            "Working on that now...",
            "Give me one sec to find that...",
            "Gathering the best info for you, one moment..."
        ]
        await self._play_filler(random.choice(fillers))

        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        from backend.agent_tools import get_worker_handler  # Reuse the Dynamic Registry
        import asyncio
        import functools
        
        db = SessionLocal()
        try:
            service = WorkerService(db)
            
            # Create Task Record
            task = service.create_task(
                workspace_id=self.workspace_id,
                worker_type=worker_type,
                input_data=parameters,
                dispatched_by_agent_id=self.agent_id
            )
            
            # Get Handler
            handler = get_worker_handler(worker_type)
            if not handler:
                service.fail_task(task.id, f"Unknown worker type: {worker_type}")
                return f"Error: Unknown worker type {worker_type}"
            
            # Execute Sync (Thread-Safe Wrapper)
            service.update_task_status(task.id, "running", current_step="Executing synchronously...", steps_completed=1, steps_total=5)
            
            loop = asyncio.get_running_loop()
            
            try:
                # Wrap the blocking call in a thread
                handler_func = functools.partial(handler, task.id, parameters, service, db)
                result = await loop.run_in_executor(None, handler_func)
                
                # Check for explicit error dict (Validation of Output)
                # "Is it responding to the user's request accurate?"
                # If error is present, it failed accuracy.
                result = self._validate_response(worker_type, result)

                if isinstance(result, dict) and "error" in result:
                    service.fail_task(task.id, result["error"])
                    return f"Worker Error: {result['error']}"
                
                # Success
                service.complete_task(task.id, result, tokens_used=0)
                service.update_task_status(task.id, "completed", current_step="Done", steps_completed=5, steps_total=5)
                
                # Return Summary (Same logic as agent_tools)
                if isinstance(result, dict):
                    if "weather_info" in result: return str(result["weather_info"])
                    if "flight_status" in result: return str(result["flight_status"])
                    if "route_info" in result: return str(result["route_info"])
                    if "summary" in result: return str(result["summary"])
                    if "jobs_found" in result: return f"Found {len(result['jobs_found'])} jobs. Top: {result['jobs_found'][0].get('title')}"
                
                return str(result)
                
            except Exception as e:
                service.fail_task(task.id, str(e))
                return f"Execution Error: {str(e)}"
                
        finally:
            db.close()

