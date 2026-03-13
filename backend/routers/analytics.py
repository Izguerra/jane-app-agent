from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from backend.database import get_db
from backend.models_db import Communication, Agent
from backend.auth import get_current_user, AuthUser, get_workspace_context

router = APIRouter(prefix="/analytics", tags=["analytics"])

class CommunicationLogResponse(BaseModel):
    id: str
    type: str
    direction: str
    status: str
    duration: int
    started_at: datetime
    # participant_identity removed as it's not in the new Communication model/schema yet
    # participant_identity: Optional[str] = None 

    model_config = ConfigDict(from_attributes=True)
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            type=obj.type,
            direction=obj.direction,
            status=obj.status,
            duration=obj.duration or 0, # Handle None
            started_at=obj.started_at,
            # participant_identity=obj.participant_identity
        )

class PaginatedLogs(BaseModel):
    items: List[CommunicationLogResponse]
    total: int

class AnalyticsSummary(BaseModel):
    total_conversations: int
    avg_duration: float
    successful_conversations: int
    total_minutes: float  # Total voice minutes used
    total_agents: int     # Total agents configured
    total_messages: int   # Total chat messages
    # Plan limits for showing consumed/total
    minutes_limit: int
    agents_limit: int
    conversations_limit: int

class DailyVolume(BaseModel):
    date: str
    count: int

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    agent_id: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    integration_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    from backend.models_db import Team
    from backend.subscription_limits import get_plan_limits
    
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)
    
    # Use direct ID in models where possible, or fetch workspace if metadata is needed
    from backend.models_db import Workspace
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    # Get plan limits
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    plan_name = team.plan_name if team else "Starter"
    limits = get_plan_limits(plan_name)
    
    # Define positive outcomes for success rate calculation
    POSITIVE_OUTCOMES = ['Information Provided', 'Appointment Booked', 'Resolved', 
                         'Appointment Rescheduled', 'Follow-up Needed']
    
    # Build a case expression for positive outcomes
    from sqlalchemy import or_
    positive_outcome_conditions = or_(
        *[Communication.call_outcome.ilike(f'%{outcome}%') for outcome in POSITIVE_OUTCOMES]
    )
    
    # Filter all queries by workspace_id
    query = db.query(
        func.count(Communication.id),
        func.avg(Communication.duration),
        func.sum(case((Communication.status == "completed", 1), else_=0)),  # Total completed
        func.sum(Communication.duration)  # Total duration in seconds
    ).filter(
        Communication.workspace_id == workspace.id
    )

    if agent_id:
        query = query.filter(Communication.agent_id == agent_id)
        
    if channel:
        query = query.filter(Communication.channel == channel)

    if integration_id:
        query = query.filter(Communication.integration_id == integration_id)

    result = query.first()
    
    total = result[0] or 0
    avg_duration = result[1] or 0.0
    completed_count = result[2] or 0
    
    # Calculate success based on POSITIVE outcomes (not just status)
    successful_query = db.query(func.count(Communication.id)).filter(
        Communication.workspace_id == workspace.id,
        Communication.status == "completed",
        positive_outcome_conditions
    )
    
    if agent_id:
        successful_query = successful_query.filter(Communication.agent_id == agent_id)
    if channel:
        successful_query = successful_query.filter(Communication.channel == channel)
    if integration_id:
        successful_query = successful_query.filter(Communication.integration_id == integration_id)
        
    successful = successful_query.scalar() or 0
    
    # Use the workspace tracked voice_minutes_this_month (this is what matters for billing)
    total_minutes = workspace.voice_minutes_this_month or 0
    
    # Count agents for this workspace
    total_agents = db.query(func.count(Agent.id)).filter(
        Agent.workspace_id == workspace.id
    ).scalar() or 0
    
    # Count chat messages (channel = 'chat' or type = 'chat')
    total_messages = db.query(func.count(Communication.id)).filter(
        Communication.workspace_id == workspace.id,
        Communication.type == "chat"
    ).scalar() or 0
    
    return AnalyticsSummary(
        total_conversations=total,
        avg_duration=float(avg_duration),
        successful_conversations=successful,
        total_minutes=round(float(total_minutes), 1),
        total_agents=total_agents,
        total_messages=total_messages,
        minutes_limit=limits["voice_minutes"],
        agents_limit=limits["chatbots"],
        conversations_limit=limits["conversations"]
    )

@router.get("/history", response_model=List[DailyVolume])
def get_analytics_history(
    agent_id: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    integration_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)
    
    today = datetime.now(timezone.utc)
    seven_days_ago = today - timedelta(days=6)
    
    # Group by date, filtered by clinic
    query = db.query(
        func.date(Communication.started_at).label('date'),
        func.count(Communication.id).label('count')
    ).filter(
        Communication.workspace_id == workspace_id,
        Communication.started_at >= seven_days_ago
    )

    if agent_id:
        query = query.filter(Communication.agent_id == agent_id)

    if channel:
        query = query.filter(Communication.channel == channel)

    if integration_id:
        query = query.filter(Communication.integration_id == integration_id)

    query = query.group_by(
        func.date(Communication.started_at)
    )
    results = query.all()
    
    # Fill in missing days
    history = []
    # Convert date objects to strings for mapping
    data_map = {str(r.date): r.count for r in results}
    
    for i in range(7):
        date = (today - timedelta(days=6-i)).strftime("%Y-%m-%d")
        history.append({
            "date": date,
            "count": data_map.get(date, 0)
        })
        
    return history

@router.get("/logs", response_model=PaginatedLogs)
def get_communication_logs(
    page: int = 1, 
    limit: int = 10,
    agent_id: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    integration_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)
    
    query = db.query(Communication).filter(Communication.workspace_id == workspace_id)
    
    if agent_id:
        query = query.filter(Communication.agent_id == agent_id)

    if channel:
        query = query.filter(Communication.channel == channel)

    if integration_id:
        query = query.filter(Communication.integration_id == integration_id)
        
    if channel:
        query = query.filter(Communication.channel == channel)
        
    total = query.count()
    
    logs = query.order_by(Communication.started_at.desc())\
        .offset((page - 1) * limit)\
        .limit(limit)\
        .all()
    
    # Convert to response model with proper field mapping
    items = [CommunicationLogResponse.from_orm(log) for log in logs]
    
    return PaginatedLogs(items=items, total=total)


