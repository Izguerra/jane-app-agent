from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Team, User, Agent, PhoneNumber
from pydantic import BaseModel
from typing import Optional
import stripe
import os
from . import data_access, billing_stats, detail_view

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

# Include sub-routers
router.include_router(data_access.router)
router.include_router(billing_stats.router)
router.include_router(detail_view.router)

class WorkspaceStatusUpdate(BaseModel):
    status: str

class WorkspaceUpdate(BaseModel):
    workspace_name: str
    owner_first_name: str
    owner_last_name: str
    owner_email: str
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    description: str | None = None
    services: str | None = None
    business_hours: str | None = None
    faq: str | None = None
    reference_urls: str | None = None

@router.get("")
def get_all_workspaces(db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    workspaces = db.query(Workspace).all()
    result = []
    for ws in workspaces:
        team = db.query(Team).filter(Team.id == ws.team_id).first()
        owner = db.execute(text("SELECT u.* FROM users u JOIN team_members tm ON u.id = tm.user_id WHERE tm.team_id = :tid LIMIT 1"), {"tid": ws.team_id}).fetchone()
        result.append({
            "id": ws.id, "name": ws.name, "owner_email": owner.email if owner else "Unknown",
            "plan": team.plan_name if team else "Starter", "status": team.subscription_status if team else "active",
            "created_at": ws.created_at.isoformat() if ws.created_at else None
        })
    result.sort(key=lambda x: x['created_at'] or '', reverse=True)
    return {"items": result, "total": len(result)}

@router.put("/{workspace_id}")
def update_workspace(workspace_id: str, update_data: WorkspaceUpdate, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace: raise HTTPException(status_code=404)
    
    workspace.name = update_data.workspace_name
    workspace.phone = update_data.phone
    workspace.address = update_data.address
    workspace.website = update_data.website
    
    # Business Profile
    for field in ["description", "services", "business_hours", "faq", "reference_urls"]:
        val = getattr(update_data, field)
        if val is not None: setattr(workspace, field, val)
    
    # Owner update
    owner_id = db.execute(text("SELECT user_id FROM team_members WHERE team_id = :tid LIMIT 1"), {"tid": workspace.team_id}).scalar()
    if owner_id:
        user = db.query(User).filter(User.id == owner_id).first()
        if user:
            user.first_name = update_data.owner_first_name
            user.last_name = update_data.owner_last_name
            user.email = update_data.owner_email
            
    db.commit()
    return {"success": True}

@router.patch("/{workspace_id}/status")
def update_workspace_status(workspace_id: str, status_update: WorkspaceStatusUpdate, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    if not team: raise HTTPException(status_code=404)
    
    # Stripe logic
    if team.stripe_subscription_id:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        try:
            if status_update.status == 'suspended':
                stripe.Subscription.modify(team.stripe_subscription_id, pause_collection={'behavior': 'void'})
            elif status_update.status == 'active':
                stripe.Subscription.modify(team.stripe_subscription_id, pause_collection='')
        except Exception as e: print(f"Stripe error: {e}")
            
    team.subscription_status = status_update.status
    db.commit()
    return {"success": True, "status": status_update.status}
