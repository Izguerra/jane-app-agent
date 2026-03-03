from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.services.crm_service import CRMService
from backend.models_db import Workspace

router = APIRouter(prefix="/crm", tags=["crm"])

@router.get("/stats")
def get_dashboard_stats(
    agent_id: str = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Role-based access control
    # Role-based access control
    # Allow members but filter data later
    if current_user.role not in ['owner', 'admin', 'member', 'supaagent_admin']:
         return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})

    # Get workspace for user's team
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        return {}
        
    service = CRMService(db)
    stats = service.get_dashboard_stats(workspace.id, agent_id=agent_id)
    
    # Filter sensitive data for members
    if current_user.role not in ['owner', 'admin', 'supaagent_admin']:
        if 'total_revenue' in stats:
            del stats['total_revenue']
        if 'total_subscribers' in stats:
            del stats['total_subscribers']
            
    return stats

@router.get("/activity")
def get_recent_activity(
    limit: int = 5,
    agent_id: str = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        return []
        
    service = CRMService(db)
    return service.get_recent_activity(workspace.id, limit=limit, agent_id=agent_id)
