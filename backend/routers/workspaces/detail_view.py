from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Team, Agent, PhoneNumber, Communication, Integration
from backend.subscription_limits import get_plan_limits
import stripe
import os
from datetime import datetime

router = APIRouter(tags=["workspaces-detail"])

@router.get("/{workspace_id}")
def get_workspace(workspace_id: str, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner', 'admin', 'member']: raise HTTPException(status_code=403)
    
    workspace = db.query(Workspace).filter((Workspace.id == workspace_id) | (Workspace.team_id == workspace_id)).first()
    if not workspace: raise HTTPException(status_code=404)
    
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    owner = db.execute(text("SELECT u.* FROM users u JOIN team_members tm ON u.id = tm.user_id WHERE tm.team_id = :tid LIMIT 1"), {"tid": workspace.team_id}).fetchone()
    
    # Aggregates
    total_convs = db.query(func.count(Communication.id)).filter(Communication.workspace_id == workspace.id).scalar() or 0
    voice_usage = db.query(func.sum(Communication.duration)).filter(Communication.workspace_id == workspace.id, Communication.type == 'call').scalar() or 0
    
    agents = db.query(Agent).filter(Agent.workspace_id == workspace.id, Agent.is_active == True).all()
    integrations = db.query(Integration).filter(Integration.workspace_id == workspace.id).all()
    
    # Billing History
    billing_history = []
    if team and team.stripe_customer_id:
        try:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            invoices = stripe.Invoice.list(customer=team.stripe_customer_id, limit=5)
            billing_history = [{"date": datetime.fromtimestamp(i.created).strftime('%x'), "amount": i.amount_paid/100, "status": i.status} for i in invoices.data]
        except: pass

    return {
        "id": workspace.id, "name": workspace.name, "team_id": workspace.team_id,
        "owner_email": owner.email if owner else None, "plan": team.plan_name if team else "Starter",
        "stats": {"total_conversations": total_convs, "voice_usage_minutes": voice_usage // 60},
        "agents": [{"id": a.id, "name": a.name} for a in agents],
        "integrations": [{"provider": i.provider, "is_active": i.is_active} for i in integrations],
        "billing_history": billing_history, "limits": get_plan_limits(team.plan_name if team else "Starter")
    }
