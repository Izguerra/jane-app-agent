from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
from backend.database import get_db
from backend.services.worker_service import WorkerService
from backend.auth import get_current_user, AuthUser
from backend.models_db import WorkerTask
from .utils import verify_workspace_access
from .models import TaskResponse, CreateTaskRequest, RateTaskRequest, CompleteTaskRequest

router = APIRouter(tags=["Worker Tasks"])

@router.post("/tasks", response_model=TaskResponse)
async def create_worker_task(
    workspace_id: str,
    request: CreateTaskRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new worker task."""
    verify_workspace_access(db, current_user, workspace_id)
    service = WorkerService(db)
    template = service.get_template_by_slug(request.worker_type)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown worker type: {request.worker_type}")
    
    task = service.create_task(workspace_id=workspace_id, worker_type=request.worker_type, input_data=request.input_data, customer_id=request.customer_id, created_by_user_id=current_user.id)
    return TaskResponse(
        id=task.id, workspace_id=task.workspace_id, worker_type=task.worker_type,
        worker_name=template.name if template else task.worker_type.title(),
        template_id=task.template_id, status=task.status, input_data=task.input_data or {},
        output_data=task.output_data, steps_completed=task.steps_completed or 0,
        steps_total=task.steps_total, current_step=task.current_step,
        error_message=task.error_message, tokens_used=task.tokens_used or 0,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )

@router.get("/tasks")
async def get_workspace_tasks(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    worker_type: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    admin: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tasks for a workspace, or all tasks (admin mode)."""
    service = WorkerService(db)
    if admin:
        if current_user.role != "supaagent_admin":
             raise HTTPException(status_code=403, detail="Admin privileges required")
        query = db.query(WorkerTask).order_by(WorkerTask.created_at.desc())
    else:
        if not workspace_id:
            if current_user.role == "worker_instance": workspace_id = current_user.team_id
            else: raise HTTPException(status_code=400, detail="workspace_id is required")
        verify_workspace_access(db, current_user, workspace_id)
        query = db.query(WorkerTask).filter(WorkerTask.workspace_id == workspace_id).order_by(WorkerTask.created_at.desc())

    if status: query = query.filter(WorkerTask.status == status)
    if worker_type: query = query.filter(WorkerTask.worker_type == worker_type)
    if customer_id: query = query.filter(WorkerTask.customer_id == customer_id)
    tasks = query.limit(limit).offset(offset).all()
    
    template_map = {t.slug: t.name for t in service.get_all_templates()}
    return {"tasks": [{
        "id": t.id, "workspace_id": t.workspace_id, "worker_type": t.worker_type,
        "worker_name": template_map.get(t.worker_type, t.worker_type.title()),
        "template_id": t.template_id, "status": t.status, "input_data": t.input_data or {},
        "output_data": t.output_data, "steps_completed": t.steps_completed or 0,
        "steps_total": t.steps_total, "current_step": t.current_step, "error_message": t.error_message,
        "tokens_used": t.tokens_used or 0, "rating": t.rating, "rating_feedback": t.rating_feedback,
        "total_fee_cents": t.total_fee_cents or 0, "created_at": t.created_at.isoformat() if t.created_at else None,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None
    } for t in tasks]}

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_worker_task(
    task_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID."""
    service = WorkerService(db)
    task = service.get_task(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    verify_workspace_access(db, current_user, task.workspace_id)
    template = service.get_template_by_slug(task.worker_type)
    return TaskResponse(
        id=str(task.id), workspace_id=task.workspace_id, worker_type=task.worker_type,
        worker_name=template.name if template else task.worker_type.title(),
        template_id=str(task.template_id) if task.template_id else None,
        status=task.status, input_data=task.input_data or {}, output_data=task.output_data,
        steps_completed=task.steps_completed or 0, steps_total=task.steps_total,
        current_step=task.current_step, error_message=task.error_message,
        tokens_used=task.tokens_used or 0, created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )

@router.post("/tasks/{task_id}/cancel")
async def cancel_worker_task(task_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel a pending or running task."""
    service = WorkerService(db)
    task = service.get_task(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    verify_workspace_access(db, current_user, task.workspace_id)
    task = service.cancel_task(task_id)
    return {"success": True, "status": task.status}

@router.get("/stats")
async def get_worker_stats(workspace_id: Optional[str] = Query(None), admin: bool = Query(False), current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get worker task statistics."""
    if admin:
        if current_user.role != "supaagent_admin": raise HTTPException(status_code=403, detail="Admin privileges required")
        query = db.query(WorkerTask)
        total_revenue = db.query(func.sum(WorkerTask.total_fee_cents)).filter(WorkerTask.fee_billed == True).scalar() or 0
        return {
            "total_tasks": query.count(),
            "running_tasks": query.filter(WorkerTask.status == "running").count(),
            "completed_tasks": query.filter(WorkerTask.status == "completed").count(),
            "failed_tasks": query.filter(WorkerTask.status == "failed").count(),
            "avg_rating": db.query(func.avg(WorkerTask.rating)).filter(WorkerTask.rating.isnot(None)).scalar(),
            "total_revenue_cents": total_revenue
        }
    if not workspace_id: raise HTTPException(status_code=400, detail="workspace_id is required")
    verify_workspace_access(db, current_user, workspace_id)
    return WorkerService(db).get_workspace_stats(workspace_id)

@router.post("/tasks/{task_id}/rate")
async def rate_worker_task(task_id: str, request: RateTaskRequest, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rate a completed worker task."""
    if request.rating < 1 or request.rating > 5: raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    task = db.query(WorkerTask).filter(WorkerTask.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    verify_workspace_access(db, current_user, task.workspace_id)
    if task.status != "completed": raise HTTPException(status_code=400, detail="Can only rate completed tasks")
    task.rating = request.rating
    task.rating_feedback = request.feedback
    task.rated_at = datetime.utcnow()
    task.rated_by_user_id = current_user.id
    db.commit()
    return {"success": True, "task_id": task_id, "rating": request.rating, "outcome_fee_applied": request.rating >= 4}

@router.post("/tasks/{task_id}/complete")
async def complete_worker_task(task_id: str, request: CompleteTaskRequest, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a worker task as completed."""
    service = WorkerService(db)
    task = service.get_task(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    verify_workspace_access(db, current_user, task.workspace_id)
    if request.status == "failed" or request.error_message:
        task = service.fail_task(task_id, request.error_message or "Unknown error")
    else:
        task = service.complete_task(task_id=task_id, output_data=request.output_data, tokens_used=request.tokens_used)
    if not task: raise HTTPException(status_code=500, detail="Failed to update task")
    return {"success": True, "status": task.status}
