from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from typing import Dict, Any

try:
    from backend.database import get_db
    from backend.models_db import Integration, Communication, Agent, Team, Workspace
except ModuleNotFoundError:
    from database import get_db
    from models_db import Integration, Communication, Agent, Team, Workspace

router = APIRouter(prefix="/admin/analytics", tags=["admin_analytics"])


@router.get("/integration-stats")
def get_integration_stats(db: Session = Depends(get_db)):
    """Get integration statistics with month-over-month growth."""
    
    # Current month start
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)
    
    # Last month start
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
    
    # Active WhatsApp integrations
    whatsapp_current = db.query(func.count(Integration.id)).filter(
        Integration.provider == 'whatsapp',
        Integration.is_active == True
    ).scalar() or 0
    
    whatsapp_last = db.query(func.count(Integration.id)).filter(
        Integration.provider == 'whatsapp',
        Integration.is_active == True,
        Integration.created_at < current_month_start
    ).scalar() or 0
    
    whatsapp_growth = ((whatsapp_current - whatsapp_last) / whatsapp_last * 100) if whatsapp_last > 0 else 0
    
    # Active Voice Agents
    voice_current = db.query(func.count(Agent.id)).filter(
        Agent.is_active == True
    ).scalar() or 0
    
    voice_last = db.query(func.count(Agent.id)).filter(
        Agent.is_active == True,
        Agent.created_at < current_month_start
    ).scalar() or 0
    
    voice_growth = ((voice_current - voice_last) / voice_last * 100) if voice_last > 0 else 0
    
    # Calendar integrations (Google + MS)
    calendar_current = db.query(func.count(Integration.id)).filter(
        Integration.provider.in_(['google_calendar', 'ms_calendar']),
        Integration.is_active == True
    ).scalar() or 0
    
    calendar_last = db.query(func.count(Integration.id)).filter(
        Integration.provider.in_(['google_calendar', 'ms_calendar']),
        Integration.is_active == True,
        Integration.created_at < current_month_start
    ).scalar() or 0
    
    calendar_growth = ((calendar_current - calendar_last) / calendar_last * 100) if calendar_last > 0 else 0
    
    # Active chat conversations (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    chats_current = db.query(func.count(func.distinct(Communication.workspace_id))).filter(
        Communication.type == 'chat',
        Communication.started_at >= thirty_days_ago
    ).scalar() or 0
    
    sixty_days_ago = now - timedelta(days=60)
    chats_last = db.query(func.count(func.distinct(Communication.workspace_id))).filter(
        Communication.type == 'chat',
        Communication.started_at >= sixty_days_ago,
        Communication.started_at < thirty_days_ago
    ).scalar() or 0
    
    chats_growth = ((chats_current - chats_last) / chats_last * 100) if chats_last > 0 else 0
    
    return {
        "whatsapp_agents": {
            "count": whatsapp_current,
            "growth_percentage": round(whatsapp_growth, 1)
        },
        "voice_agents": {
            "count": voice_current,
            "growth_percentage": round(voice_growth, 1)
        },
        "calendar_integrations": {
            "count": calendar_current,
            "growth_percentage": round(calendar_growth, 1)
        },
        "active_chats": {
            "count": chats_current,
            "growth_percentage": round(chats_growth, 1)
        }
    }


@router.get("/api-usage")
def get_api_usage(db: Session = Depends(get_db)):
    """Get API usage statistics across all integrations."""
    
    # AI/LLM usage (count of communications - each uses AI)
    ai_usage = db.query(func.count(Communication.id)).scalar() or 0
    
    # WhatsApp usage
    whatsapp_usage = db.query(func.count(Communication.id)).filter(
        Communication.channel == 'whatsapp'
    ).scalar() or 0
    
    # Calendar API calls (estimate based on integrations * average calls)
    calendar_integrations = db.query(func.count(Integration.id)).filter(
        Integration.provider.in_(['google_calendar', 'ms_calendar']),
        Integration.is_active == True
    ).scalar() or 0
    calendar_usage = calendar_integrations * 100  # Estimate
    
    # Voice minutes
    voice_minutes = db.query(func.sum(Communication.duration)).filter(
        Communication.type == 'call'
    ).scalar() or 0
    
    return {
        "ai_llm_calls": ai_usage,
        "whatsapp_messages": whatsapp_usage,
        "calendar_api_calls": calendar_usage,
        "voice_minutes": voice_minutes
    }


@router.get("/revenue")
def get_revenue_stats(db: Session = Depends(get_db)):
    """Get revenue statistics."""
    
    # Count active subscriptions by plan
    starter_count = db.query(func.count(Team.id)).filter(
        Team.plan_name == 'Starter',
        Team.subscription_status == 'active'
    ).scalar() or 0
    
    pro_count = db.query(func.count(Team.id)).filter(
        Team.plan_name == 'Professional',
        Team.subscription_status == 'active'
    ).scalar() or 0
    
    enterprise_count = db.query(func.count(Team.id)).filter(
        Team.plan_name == 'Enterprise',
        Team.subscription_status == 'active'
    ).scalar() or 0
    
    # Calculate MRR (Monthly Recurring Revenue)
    # Starter: $49, Pro: $99, Enterprise: $299
    total_mrr = (starter_count * 49) + (pro_count * 99) + (enterprise_count * 299)
    
    return {
        "total_mrr": total_mrr,
        "starter_count": starter_count,
        "pro_count": pro_count,
        "enterprise_count": enterprise_count
    }


@router.get("/customers")
def get_customer_stats(db: Session = Depends(get_db)):
    """Get customer statistics."""
    
    # Total workspaces
    total_workspaces = db.query(func.count(Workspace.id)).scalar() or 0
    
    # Active subscriptions
    active_subs = db.query(func.count(Team.id)).filter(
        Team.subscription_status == 'active'
    ).scalar() or 0
    
    return {
        "total_workspaces": total_workspaces,
        "active_subscriptions": active_subs
    }


@router.get("/voice-interactions")
def get_voice_interactions(db: Session = Depends(get_db)):
    """Get voice interaction volume for the last 7 days."""
    now = datetime.now()
    
    # Get data for last 7 days
    daily_data = []
    for i in range(6, -1, -1):  # 7 days ago to today
        day = now - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(func.count(Communication.id)).filter(
            Communication.type == 'call',
            Communication.started_at >= day_start,
            Communication.started_at < day_end
        ).scalar() or 0
        
        daily_data.append({
            "date": day.strftime("%d %b"),
            "count": count,
            "is_today": i == 0
        })
    
    return {"daily_data": daily_data}


@router.get("/recent-activations")
def get_recent_activations(db: Session = Depends(get_db)):
    """Get recent integration activations."""
    recent = db.query(Integration).filter(
        Integration.is_active == True
    ).order_by(Integration.created_at.desc()).limit(5).all()
    
    activations = []
    for integration in recent:
        # Get workspace info
        workspace = db.query(Workspace).filter(Workspace.id == integration.workspace_id).first()
        
        # Calculate time ago
        created = integration.created_at
        now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
        diff = now - created
        
        if diff.days > 0:
            time_ago = f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            time_ago = f"{diff.seconds // 3600}h ago"
        else:
            time_ago = f"{diff.seconds // 60}m ago"
        
        activations.append({
            "provider": integration.provider,
            "workspace_name": workspace.name if workspace else "Unknown",
            "time_ago": time_ago
        })
    
    return {"activations": activations}
