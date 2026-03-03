"""
Worker Service

Service layer for managing autonomous worker agents.
Handles task creation, execution, status tracking, and results.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Handle both import contexts
try:
    from backend.models_db import WorkerTemplate, WorkerTask
except ModuleNotFoundError:
    from models_db import WorkerTemplate, WorkerTask


class WorkerService:
    """
    Service for managing worker tasks.
    
    Usage:
        service = WorkerService(db_session)
        task = service.create_task(
            workspace_id="ws_123",
            worker_type="job-search",
            input_data={"job_title": "Software Engineer", "location": "Remote"}
        )
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # =========================================================================
    # TEMPLATE OPERATIONS
    # =========================================================================
    
    def get_all_templates(self, active_only: bool = True) -> List[WorkerTemplate]:
        """Get all available worker templates."""
        query = self.db.query(WorkerTemplate)
        if active_only:
            query = query.filter(WorkerTemplate.is_active == True)
        return query.order_by(WorkerTemplate.category, WorkerTemplate.name).all()
    
    def get_template_by_slug(self, slug: str) -> Optional[WorkerTemplate]:
        """Get a worker template by its slug."""
        return self.db.query(WorkerTemplate).filter(WorkerTemplate.slug == slug).first()
    
    def get_template_schema(self, slug: str) -> Dict[str, Any]:
        """Get the parameter schema for a worker template (for dynamic forms)."""
        template = self.get_template_by_slug(slug)
        if template:
            return template.parameter_schema or {}
        return {}
    
    # =========================================================================
    # TASK OPERATIONS
    # =========================================================================
    
    def create_task(
        self,
        workspace_id: str,
        worker_type: str,
        input_data: Dict[str, Any],
        customer_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
        dispatched_by_agent_id: Optional[str] = None
    ) -> WorkerTask:
        """
        Create a new worker task.
        
        Args:
            workspace_id: The workspace this task belongs to
            worker_type: Slug of the worker type (e.g., 'job-search')
            input_data: Parameters for the task (validated against schema)
            customer_id: Optional customer context
            created_by_user_id: User who triggered the task
            dispatched_by_agent_id: ID of the agent (voice/chat) that dispatched this task
            
        Returns:
            The created WorkerTask
        """
        # Alias handling for common hallucinations or legacy names
        if worker_type == "email-sender":
            worker_type = "email-worker"
            
        # Get template for additional configuration
        template = self.get_template_by_slug(worker_type)
        template_id = template.id if template else None
        
        task = WorkerTask(
            id=str(uuid4()),
            workspace_id=workspace_id,
            template_id=template_id,
            worker_type=worker_type,
            customer_id=customer_id,
            created_by_user_id=created_by_user_id,
            dispatched_by_agent_id=dispatched_by_agent_id,
            status="pending",
            input_data=input_data,
            logs=[]
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[WorkerTask]:
        """Get a task by ID."""
        return self.db.query(WorkerTask).filter(WorkerTask.id == task_id).first()
    
    def get_workspace_tasks(
        self,
        workspace_id: str,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkerTask]:
        """Get tasks for a workspace with optional status and customer filter."""
        query = self.db.query(WorkerTask).filter(WorkerTask.workspace_id == workspace_id)
        
        if status:
            query = query.filter(WorkerTask.status == status)
            
        if customer_id:
            query = query.filter(WorkerTask.customer_id == customer_id)
        
        return query.order_by(desc(WorkerTask.created_at)).offset(offset).limit(limit).all()
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        current_step: Optional[str] = None,
        steps_completed: Optional[int] = None,
        steps_total: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[WorkerTask]:
        """Update task status and progress."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.status = status
        
        if current_step is not None:
            task.current_step = current_step
        if steps_completed is not None:
            task.steps_completed = steps_completed
        if steps_total is not None:
            task.steps_total = steps_total
        if error_message is not None:
            task.error_message = error_message
        
        # Set timing based on status
        if status == "running" and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ("completed", "failed", "cancelled"):
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def add_task_log(
        self,
        task_id: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkerTask]:
        """Add a log entry to a task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        if data:
            log_entry["data"] = data
        
        # Append to logs
        current_logs = task.logs or []
        current_logs.append(log_entry)
        task.logs = current_logs
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def complete_task(
        self,
        task_id: str,
        output_data: Dict[str, Any],
        tokens_used: int = 0,
        api_calls: Optional[Dict[str, int]] = None
    ) -> Optional[WorkerTask]:
        """Mark a task as completed with output data."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.status = "completed"
        task.output_data = output_data
        task.completed_at = datetime.utcnow()
        task.tokens_used = tokens_used
        
        if api_calls:
            task.api_calls = api_calls
        
        self.db.commit()
        
        # Trigger Outcome Evaluation
        try:
            from backend.services.evaluator_service import EvaluatorService
            evaluator = EvaluatorService(self.db)
            evaluator.evaluate_task(task.id)
        except Exception as e:
            print(f"Error triggering evaluator: {e}")
            
        self.db.refresh(task)
        
        return task
    
    def fail_task(self, task_id: str, error_message: str) -> Optional[WorkerTask]:
        """Mark a task as failed with an error message."""
        return self.update_task_status(
            task_id=task_id,
            status="failed",
            error_message=error_message
        )
    
    def cancel_task(self, task_id: str) -> Optional[WorkerTask]:
        """Cancel a pending or running task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        if task.status in ("pending", "running"):
            task.status = "cancelled"
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
        
        return task
    
    # =========================================================================
    # ANALYTICS / STATS
    # =========================================================================
    
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get worker task statistics for a workspace."""
        from sqlalchemy import func
        
        # Count by status
        status_counts = self.db.query(
            WorkerTask.status,
            func.count(WorkerTask.id)
        ).filter(
            WorkerTask.workspace_id == workspace_id
        ).group_by(WorkerTask.status).all()
        
        # Total tokens used
        total_tokens = self.db.query(
            func.sum(WorkerTask.tokens_used)
        ).filter(
            WorkerTask.workspace_id == workspace_id
        ).scalar() or 0
        
        return {
            "status_counts": {status: count for status, count in status_counts},
            "total_tasks": sum(count for _, count in status_counts),
            "total_tokens_used": total_tokens
        }
