"""
Workers API Router

Endpoints for managing worker templates and tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from backend.database import get_db
from backend.services.worker_service import WorkerService
from backend.services.worker_provisioner import WorkerProvisioner
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Team

router = APIRouter(prefix="/workers", tags=["Workers"])


# =========================================================================
# Pydantic Models
# =========================================================================

class WorkerTemplateResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    parameter_schema: Dict[str, Any]
    required_tools: List[str]
    required_integrations: List[str]
    icon: str
    color: str
    is_active: bool
    
    class Config:
        from_attributes = True


class CreateTaskRequest(BaseModel):
    worker_type: str
    input_data: Dict[str, Any]
    customer_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    worker_type: str
    worker_name: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    steps_completed: int
    steps_total: Optional[int] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskStatsResponse(BaseModel):
    status_counts: Dict[str, int]
    total_tasks: int
    total_tokens_used: int


class CreateInstanceRequest(BaseModel):
    worker_type: str = "openclaw"
    tier: str = "standard"
    name: Optional[str] = None
    llm_model: str = "claude-3-5-sonnet"
    llm_api_key: Optional[str] = None


class InstanceResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    worker_type: str
    tier: str
    files_disk_size_gb: int
    status: str
    container_id: Optional[str] = None
    ip_address: Optional[str] = None
    is_external: bool = False
    connection_url: Optional[str] = None
    monthly_cost_cents: int
    created_at: str

    class Config:
        from_attributes = True


# =========================================================================
# Helper: Verify Workspace Access
# =========================================================================

def verify_workspace_access(db: Session, user: AuthUser, workspace_id: str):
    """
    Ensure the user belongs to the team that owns the workspace.
    Admins can access everything if needed, but specifically for 'admin' mode endpoints.
    """
    if not workspace_id:
        return
        
    workspace = None
    if workspace_id.startswith("tm_") or workspace_id.startswith("org_"):
        workspace = db.query(Workspace).filter(Workspace.team_id == workspace_id).first()
    else:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    if not workspace:
        # If lookup by Team ID failed, maybe it's a new team that needs a workspace
        if workspace_id.startswith("tm_") or workspace_id.startswith("org_"):
             # We might want to auto-create here, but safer to let agents.py handle it or return 404
             # Let's check if the team exists at least
             team = db.query(Team).filter(Team.id == workspace_id).first()
             if team:
                 # Auto-create workspace if team exists but no workspace found (consistency fix)
                 from backend.database import generate_workspace_id
                 workspace = Workspace(
                     id=generate_workspace_id(),
                     team_id=team.id,
                     name=f"Workspace for {team.id}",
                     is_active=True
                 )
                 db.add(workspace)
                 db.commit()
                 db.refresh(workspace)
             else:
                 raise HTTPException(status_code=404, detail="Workspace not found (Invalid Team ID)")
        else:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
    if str(workspace.team_id) != str(user.team_id):
        # Fallback: Check if user is a member of this team in the DB
        # This handles cases where user.team_id (from token) might be stale or context switching didn't update token
        from backend.models_db import TeamMember
        membership = db.query(TeamMember).filter(
            TeamMember.user_id == user.id,
            TeamMember.team_id == workspace.team_id
        ).first()

        # Also check if user is supaagent_admin
        if not membership and user.role != "supaagent_admin":
             # Double check: maybe the user IS the owner of the team (if TeamMember isn't used for owners in legacy)
             # But for now, we assume failure.
             raise HTTPException(status_code=403, detail=f"Not authorized. User team: {user.team_id}, Workspace team: {workspace.team_id}")



# =========================================================================
# Template Endpoints
# =========================================================================

@router.get("/templates")
async def get_worker_templates(
    active_only: bool = Query(True, description="Only return active templates"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available worker templates."""
    service = WorkerService(db)
    templates = service.get_all_templates(active_only=active_only)
    
    # Convert UUID to string for JSON serialization
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "description": t.description,
            "category": t.category,
            "parameter_schema": t.parameter_schema or {},
            "required_tools": t.required_tools or [],
            "required_integrations": t.required_integrations or [],
            "icon": t.icon,
            "color": t.color,
            "is_active": t.is_active
        }
        for t in templates
    ]


@router.get("/templates/{slug}")
async def get_worker_template(
    slug: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific worker template by slug."""
    service = WorkerService(db)
    template = service.get_template_by_slug(slug)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    
    # Convert UUID to string for JSON serialization
    return {
        "id": str(template.id),
        "name": template.name,
        "slug": template.slug,
        "description": template.description,
        "category": template.category,
        "parameter_schema": template.parameter_schema or {},
        "required_tools": template.required_tools or [],
        "required_integrations": template.required_integrations or [],
        "icon": template.icon,
        "color": template.color,
        "is_active": template.is_active
    }


@router.get("/templates/{slug}/schema")
async def get_template_schema(
    slug: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the parameter schema for a worker template (for dynamic form generation)."""
    service = WorkerService(db)
    schema = service.get_template_schema(slug)
    if not schema:
        raise HTTPException(status_code=404, detail="Worker template not found")
    return schema


# =========================================================================
# Instance Management Endpoints (Infrastructure)
# =========================================================================

@router.get("/instances", response_model=List[InstanceResponse])
async def get_worker_instances(
    workspace_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active worker instances for a workspace."""
    verify_workspace_access(db, current_user, workspace_id)
    
    provisioner = WorkerProvisioner(db)
    instances = provisioner.get_instances(workspace_id)
    
    return [
        InstanceResponse(
            id=i.id,
            workspace_id=i.workspace_id,
            name=i.name,
            worker_type=i.worker_type,
            tier=i.tier or "standard",
            files_disk_size_gb=i.files_disk_size_gb or 10,
            status=i.status,
            container_id=i.container_id,
            ip_address=i.ip_address,
            is_external=i.is_external,
            connection_url=i.connection_url,
            monthly_cost_cents=i.monthly_cost_cents,
            created_at=i.created_at.isoformat()
        )
        for i in instances
    ]


@router.post("/instances", response_model=InstanceResponse)
async def provision_worker_instance(
    workspace_id: str,
    request: CreateInstanceRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Provision a new worker instance (Scale Up)."""
    verify_workspace_access(db, current_user, workspace_id)
    
    provisioner = WorkerProvisioner(db)
    
    try:
        instance = await provisioner.provision_instance(
            workspace_id=workspace_id,
            worker_type=request.worker_type,
            tier=request.tier,
            name=request.name,
            llm_model=request.llm_model,
            llm_api_key=request.llm_api_key
        )
        
        return InstanceResponse(
            id=instance.id,
            workspace_id=instance.workspace_id,
            name=instance.name,
            worker_type=instance.worker_type,
            tier=instance.tier or "standard",
            files_disk_size_gb=instance.files_disk_size_gb or 10,
            status=instance.status,
            container_id=instance.container_id,
            ip_address=instance.ip_address,
            monthly_cost_cents=instance.monthly_cost_cents,
            created_at=instance.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/instances/{instance_id}")
async def terminate_worker_instance(
    instance_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminate and remove a worker instance."""
    # Need to look up instance first to check permission
    from backend.models_db import WorkerInstance
    instance = db.query(WorkerInstance).filter(WorkerInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
        
    verify_workspace_access(db, current_user, instance.workspace_id)
    
    provisioner = WorkerProvisioner(db)
    success = provisioner.terminate_instance(instance_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Instance not found")
        
    return {"success": True}

# =========================================================================
# Task Endpoints
# =========================================================================

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
    
    # Validate that the worker type exists
    template = service.get_template_by_slug(request.worker_type)
    if not template:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown worker type: {request.worker_type}"
        )
    
    task = service.create_task(
        workspace_id=workspace_id,
        worker_type=request.worker_type,
        input_data=request.input_data,
        customer_id=request.customer_id,
        created_by_user_id=current_user.id
    )
    
    # Convert datetime to ISO string for response
    response = TaskResponse(
        id=task.id,
        workspace_id=task.workspace_id,
        worker_type=task.worker_type,
        worker_name=template.name if template else request.worker_type.replace("-", " ").title(),
        template_id=task.template_id,
        status=task.status,
        input_data=task.input_data or {},
        output_data=task.output_data,
        steps_completed=task.steps_completed or 0,
        steps_total=task.steps_total,
        current_step=task.current_step,
        error_message=task.error_message,
        tokens_used=task.tokens_used or 0,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )
    
    return response


@router.get("/tasks")
async def get_workspace_tasks(
    workspace_id: Optional[str] = Query(None, description="Workspace ID (omit for admin all-workspace view)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    worker_type: Optional[str] = Query(None, description="Filter by worker type"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    admin: bool = Query(False, description="Admin mode - get tasks from all workspaces"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tasks for a workspace, or all tasks (admin mode)."""
    from backend.models_db import WorkerTask
    
    service = WorkerService(db)
    
    if admin:
        # Admin access check
        if current_user.role != "supaagent_admin":
             raise HTTPException(status_code=403, detail="Admin privileges required")
             
        # Admin mode - get all tasks across all workspaces
        query = db.query(WorkerTask).order_by(WorkerTask.created_at.desc())
        if status:
            query = query.filter(WorkerTask.status == status)
        if worker_type:
            query = query.filter(WorkerTask.worker_type == worker_type)
        # Note: customer_id filter not implemented for admin ALL view effectively, but could be added.
        # Keeping it simple for admin view.
        if customer_id:
             query = query.filter(WorkerTask.customer_id == customer_id)
        tasks = query.limit(limit).offset(offset).all()
    else:
        if not workspace_id:
            # If authorized as a worker, we might have workspace_id in the user object (team_id)
            if current_user.role == "worker_instance":
                workspace_id = current_user.team_id
            else:
                raise HTTPException(status_code=400, detail="workspace_id is required for non-admin requests")
            
        verify_workspace_access(db, current_user, workspace_id)
        
        # We need to extend service.get_workspace_tasks to support worker_type or filter manually
        # Ideally, we pass it down. For now, let's filter the query manually here since get_workspace_tasks might be limited.
        # Actually, let's check what get_workspace_tasks does. 
        # Since I can't see get_workspace_tasks impl here easily, let's use a direct query for filtering if needed,
        # OR just filter the result if the list is small. 
        # But better to use the service if it supports it.
        # Let's assume service.get_workspace_tasks DOES NOT support worker_type yet.
        # So I will query DB directly here to be safe and consistent with Admin view logic,
        # OR update service.
        
        # Let's update the SERVICE usage. 
        # Since I cannot see valid service method signature, I'll rewrite this part to use DB query directly 
        # which is safer than guessing service method signature.
        
        query = db.query(WorkerTask).filter(WorkerTask.workspace_id == workspace_id).order_by(WorkerTask.created_at.desc())
        
        if status:
            query = query.filter(WorkerTask.status == status)
        
        if worker_type:
            query = query.filter(WorkerTask.worker_type == worker_type)
            
        if customer_id:
            query = query.filter(WorkerTask.customer_id == customer_id)
            
        tasks = query.limit(limit).offset(offset).all()

    
    # Pre-fetch templates to map slugs to names
    all_templates = service.get_all_templates()
    template_map = {t.slug: t.name for t in all_templates}

    # Convert to response dicts with all fields including rating/pricing
    responses = []
    for task in tasks:
        worker_name = template_map.get(task.worker_type, task.worker_type.replace("-", " ").title())
        responses.append({
            "id": task.id,
            "workspace_id": task.workspace_id,
            "worker_type": task.worker_type,
            "worker_name": worker_name,
            "template_id": task.template_id,
            "status": task.status,
            "input_data": task.input_data or {},
            "output_data": task.output_data,
            "steps_completed": task.steps_completed or 0,
            "steps_total": task.steps_total,
            "current_step": task.current_step,
            "error_message": task.error_message,
            "tokens_used": task.tokens_used or 0,
            "rating": task.rating,
            "rating_feedback": task.rating_feedback,
            "total_fee_cents": task.total_fee_cents or 0,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        })
    
    return {"tasks": responses}



@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_worker_task(
    task_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID."""
    service = WorkerService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    verify_workspace_access(db, current_user, task.workspace_id)
    
    # Fetch worker name
    template = service.get_template_by_slug(task.worker_type)
    worker_name = template.name if template else task.worker_type.replace("-", " ").title()

    try:
        return TaskResponse(
            id=str(task.id),
            workspace_id=task.workspace_id,
            worker_type=task.worker_type,
            worker_name=worker_name,
            template_id=str(task.template_id) if task.template_id else None,
            status=task.status,
            input_data=task.input_data or {},
            output_data=task.output_data,
            steps_completed=task.steps_completed or 0,
            steps_total=task.steps_total,
            current_step=task.current_step,
            error_message=task.error_message,
            tokens_used=task.tokens_used or 0,
            created_at=task.created_at.isoformat() if task.created_at else None,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Serialization Error: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_worker_task(
    task_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending or running task."""
    service = WorkerService(db)
    task = service.get_task(task_id) # Need to fetch to check permissions
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    verify_workspace_access(db, current_user, task.workspace_id)
    
    task = service.cancel_task(task_id)
    return {"success": True, "status": task.status}


@router.get("/stats")
async def get_worker_stats(
    workspace_id: Optional[str] = Query(None, description="Workspace ID (omit for admin global stats)"),
    admin: bool = Query(False, description="Admin mode - get global stats"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get worker task statistics for a workspace or globally (admin)."""
    from backend.models_db import WorkerTask
    from sqlalchemy import func
    
    service = WorkerService(db)
    
    if admin:
        if current_user.role != "supaagent_admin":
             raise HTTPException(status_code=403, detail="Admin privileges required")
             
        # Global stats for admin
        query = db.query(WorkerTask)
        
        total_tasks = query.count()
        running_tasks = query.filter(WorkerTask.status == "running").count()
        completed_tasks = query.filter(WorkerTask.status == "completed").count()
        failed_tasks = query.filter(WorkerTask.status == "failed").count()
        
        # Calculate average rating
        avg_rating_result = db.query(func.avg(WorkerTask.rating)).filter(WorkerTask.rating.isnot(None)).scalar()
        avg_rating = float(avg_rating_result) if avg_rating_result else None
        
        # Calculate total revenue
        total_revenue = db.query(func.sum(WorkerTask.total_fee_cents)).filter(WorkerTask.fee_billed == True).scalar() or 0
        
        return {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "avg_rating": avg_rating,
            "total_revenue_cents": total_revenue
        }
    else:
        if not workspace_id:
            raise HTTPException(status_code=400, detail="workspace_id is required for non-admin requests")
            
        verify_workspace_access(db, current_user, workspace_id)
        
        stats = service.get_workspace_stats(workspace_id)
        return stats



class RateTaskRequest(BaseModel):
    rating: int
    feedback: Optional[str] = None


@router.post("/tasks/{task_id}/rate")
async def rate_worker_task(
    task_id: str,
    request: RateTaskRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rate a completed worker task.
    
    Ratings:
    - 1-2 stars: Below expectations (no outcome fee)
    - 3 stars: Met expectations (no outcome fee)
    - 4-5 stars: Exceeded expectations (outcome fee applies)
    """
    from backend.models_db import WorkerTask
    from datetime import datetime
    
    # Validate rating
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    task = db.query(WorkerTask).filter(WorkerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    verify_workspace_access(db, current_user, task.workspace_id)
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Can only rate completed tasks")
    
    # Update task with rating
    task.rating = request.rating
    task.rating_feedback = request.feedback
    task.rated_at = datetime.utcnow()
    task.rated_by_user_id = current_user.id
    
    # TODO: Calculate outcome fee if rating >= 4
    # This would integrate with billing service
    
    db.commit()
    db.refresh(task)
    
    return {
        "success": True,
        "task_id": task_id,
        "rating": request.rating,
        "outcome_fee_applied": request.rating >= 4
    }


class CompleteTaskRequest(BaseModel):
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    status: str = "completed"
    tokens_used: int = 0


@router.post("/tasks/{task_id}/complete")
async def complete_worker_task(
    task_id: str,
    request: CompleteTaskRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a worker task as completed (called by the worker itself).
    """
    service = WorkerService(db)
    
    # Check permissions
    # In a real scenario, this would check if the user is a worker or has worker scopes.
    # For now, we rely on the fact that we're using a user token for the test.
    # Ideally, we verify the user belongs to the same workspace as the task.
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    verify_workspace_access(db, current_user, task.workspace_id)
    
    if request.status == "failed" or request.error_message:
        task = service.fail_task(task_id, request.error_message or "Unknown error")
    else:
        task = service.complete_task(
            task_id=task_id,
            output_data=request.output_data,
            tokens_used=request.tokens_used
        )
        
    if not task:
        raise HTTPException(status_code=500, detail="Failed to update task")

    return {"success": True, "status": task.status}
