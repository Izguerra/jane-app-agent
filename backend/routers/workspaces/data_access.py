from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, text, func, case, or_
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Communication, Appointment, Campaign, WorkerTask, Agent, Team
from backend.services.crm_service import CRMService
from backend.services.worker_service import WorkerService
from backend.subscription_limits import get_plan_limits
from typing import Optional
import stripe
import os
from datetime import datetime, timedelta

router = APIRouter(tags=["workspaces-data"])

@router.get("/{workspace_id}/customers")
def get_workspace_customers(workspace_id: str, page: int = 1, limit: int = 10, search: str = None, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    service = CRMService(db)
    return service.get_customers(workspace_id, skip=(page-1)*limit, limit=limit, search=search)

@router.get("/{workspace_id}/communications")
def get_workspace_communications(workspace_id: str, type: str = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    query = db.query(Communication).filter(Communication.workspace_id == workspace_id)
    if type and type != 'all': query = query.filter(Communication.type == type)
    return {"total": query.count(), "items": query.order_by(desc(Communication.started_at)).offset(offset).limit(limit).all()}

@router.get("/{workspace_id}/appointments")
def get_workspace_appointments(workspace_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    query = db.query(Appointment).filter(Appointment.workspace_id == workspace_id)
    return {"total": query.count(), "items": query.order_by(desc(Appointment.appointment_date)).offset(offset).limit(limit).all()}

@router.get("/{workspace_id}/tasks")
def get_workspace_tasks(workspace_id: str, page: int = 1, limit: int = 20, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    query = db.query(WorkerTask).filter(WorkerTask.workspace_id == workspace_id)
    return {"tasks": query.order_by(desc(WorkerTask.created_at)).offset((page-1)*limit).limit(limit).all(), "total": query.count()}

@router.get("/{workspace_id}/analytics/summary")
def get_workspace_analytics_summary(workspace_id: str, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role not in ['supaagent_admin', 'owner']: raise HTTPException(status_code=403)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace: return {}
    
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    limits = get_plan_limits(team.plan_name if team else "Starter")
    
    stats = db.query(func.count(Communication.id), func.avg(Communication.duration), func.sum(Communication.duration)).filter(Communication.workspace_id == workspace_id).first()
    
    return {
        "total_conversations": stats[0] or 0, "avg_duration": float(stats[1] or 0),
        "total_minutes": round(float(workspace.voice_minutes_this_month or 0), 1),
        "minutes_limit": limits["voice_minutes"], "agents_limit": limits["chatbots"]
    }
