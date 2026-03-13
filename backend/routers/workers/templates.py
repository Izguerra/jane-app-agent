from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.worker_service import WorkerService
from backend.auth import get_current_user, AuthUser

router = APIRouter(tags=["Worker Templates"])

@router.get("/templates")
async def get_worker_templates(
    active_only: bool = Query(True, description="Only return active templates"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available worker templates."""
    service = WorkerService(db)
    templates = service.get_all_templates(active_only=active_only)
    return [
        {
            "id": str(t.id), "name": t.name, "slug": t.slug, "description": t.description,
            "category": t.category, "parameter_schema": t.parameter_schema or {},
            "required_tools": t.required_tools or [], "required_integrations": t.required_integrations or [],
            "icon": t.icon, "color": t.color, "is_active": t.is_active
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
    
    return {
        "id": str(template.id), "name": template.name, "slug": template.slug, "description": template.description,
        "category": template.category, "parameter_schema": template.parameter_schema or {},
        "required_tools": template.required_tools or [], "required_integrations": template.required_integrations or [],
        "icon": template.icon, "color": template.color, "is_active": template.is_active
    }

@router.get("/templates/{slug}/schema")
async def get_template_schema(
    slug: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the parameter schema for a worker template."""
    service = WorkerService(db)
    schema = service.get_template_schema(slug)
    if not schema:
        raise HTTPException(status_code=404, detail="Worker template not found")
    return schema
