import time
import asyncio
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService

class OpenClawWorker:
    """
    Worker handler for OpenClaw.
    Since OpenClaw runs in a separate container and polls for tasks,
    this synchronous handler just waits (polls) for the task to be 
    marked as completed or failed by the container worker.
    """
    
    @staticmethod
    def run(task_id: str, input_data: Dict[str, Any], service: WorkerService, db: Session) -> Dict[str, Any]:
        """
        Synchronous wrapper that waits for the external container to finish the task.
        """
        timeout = 60 # 60 seconds max wait for browser tasks
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Refresh task from DB
            from backend.models_db import WorkerTask
            task = db.query(WorkerTask).filter(WorkerTask.id == task_id).first()
            
            if not task:
                return {"error": f"Task {task_id} disappeared."}
            
            if task.status == "completed":
                return task.output_data or {"summary": "Task completed with no output."}
            
            if task.status == "failed":
                return {"error": task.error_message or "Task failed without error message."}
            
            # Use small sleep to avoid hammered DB
            time.sleep(2)
            
        return {"error": f"Task timed out after {timeout}s waiting for container worker."}
