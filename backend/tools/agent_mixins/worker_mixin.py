from livekit.agents import llm
from backend.database import SessionLocal
from backend.services.worker_service import WorkerService
import json
import asyncio
import functools

class WorkerMixin:
    @llm.function_tool(description="Execute a task IMMEDIATELY and return the result.")
    async def run_task_now(self, worker_type: str, input_data: str):
        db = SessionLocal()
        try:
            service = WorkerService(db)
            params = json.loads(input_data)
            
            if "workspace_id" not in params:
                params["workspace_id"] = self.workspace_id
                
            task = service.create_task(workspace_id=self.workspace_id, worker_type=worker_type, input_data=params, dispatched_by_agent_id=self.agent_id)
            
            # Simplified handler resolution for refactor
            from backend.agent_tools import get_worker_handler
            handler = get_worker_handler(worker_type)
            if not handler: return f"Error: Unknown worker {worker_type}"
            
            loop = asyncio.get_running_loop()
            handler_func = functools.partial(handler, task.id, params, service, db)
            result = await loop.run_in_executor(None, handler_func)
            
            service.complete_task(task.id, result)
            return str(result)
        finally: db.close()

    @llm.function_tool(description="Check the status of a previously dispatched worker task.")
    async def check_agent_task_status(self, task_id: str):
        db = SessionLocal()
        try:
            service = WorkerService(db)
            task = service.get_task(task_id)
            if not task: return "Task not found."
            return f"Status: {task.status.upper()}. Result: {task.output_data}"
        finally: db.close()
