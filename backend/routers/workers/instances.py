from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.services.worker_provisioner import WorkerProvisioner
from backend.auth import get_current_user, AuthUser
from backend.models_db import WorkerInstance
from .utils import verify_workspace_access
from .models import InstanceResponse, CreateInstanceRequest

router = APIRouter(tags=["Worker Instances"])

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
            id=i.id, workspace_id=i.workspace_id, name=i.name, worker_type=i.worker_type,
            tier=i.tier or "standard", files_disk_size_gb=i.files_disk_size_gb or 10,
            status=i.status, container_id=i.container_id, ip_address=i.ip_address,
            is_external=i.is_external, connection_url=i.connection_url,
            monthly_cost_cents=i.monthly_cost_cents, created_at=i.created_at.isoformat()
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
            workspace_id=workspace_id, worker_type=request.worker_type, tier=request.tier,
            name=request.name, llm_model=request.llm_model, llm_api_key=request.llm_api_key
        )
        return InstanceResponse(
            id=instance.id, workspace_id=instance.workspace_id, name=instance.name,
            worker_type=instance.worker_type, tier=instance.tier or "standard",
            files_disk_size_gb=instance.files_disk_size_gb or 10, status=instance.status,
            container_id=instance.container_id, ip_address=instance.ip_address,
            monthly_cost_cents=instance.monthly_cost_cents, created_at=instance.created_at.isoformat()
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
    instance = db.query(WorkerInstance).filter(WorkerInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
        
    verify_workspace_access(db, current_user, instance.workspace_id)
    provisioner = WorkerProvisioner(db)
    if not provisioner.terminate_instance(instance_id):
        raise HTTPException(status_code=404, detail="Instance not found")
    return {"success": True}
