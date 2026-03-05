from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Team, User, Agent, PhoneNumber, Communication, Appointment, Campaign
from backend.services.crm_service import CRMService
from backend.services.campaign_service import CampaignService
from backend.services.worker_service import WorkerService
from backend.subscription_limits import get_plan_limits
import stripe
import os
from datetime import datetime

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

class WorkspaceStatusUpdate(BaseModel):
    status: str  # 'active', 'suspended', 'canceled'

class WorkspaceUpdate(BaseModel):
    workspace_name: str
    owner_first_name: str
    owner_last_name: str
    owner_email: str
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    # Business Profile Fields
    description: str | None = None
    services: str | None = None
    business_hours: str | None = None
    faq: str | None = None
    reference_urls: str | None = None

@router.get("")
def get_all_workspaces(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get all workspaces (admin only)."""
    # Check if user is admin
    if current_user.role not in ['supaagent_admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all workspaces with aggregated data
    workspaces = db.query(Workspace).all()
    
    result = []
    for workspace in workspaces:
        # Get team info
        team = db.query(Team).filter(Team.id == workspace.team_id).first()
        
        # Get owner info (query team_members to find user)
        owner_query = db.execute(
            text("""
                SELECT u.* FROM users u 
                JOIN team_members tm ON u.id = tm.user_id 
                WHERE tm.team_id = :team_id 
                LIMIT 1
            """),
            {"team_id": workspace.team_id}
        ).fetchone()
        
        # Count agents
        agent_count = db.query(func.count(Agent.id)).filter(
            Agent.workspace_id == workspace.id
        ).scalar() or 0
        
        # Count phone numbers
        phone_count = db.query(func.count(PhoneNumber.id)).filter(
            PhoneNumber.workspace_id == workspace.id
        ).scalar() or 0
        
        # Get usage stats (mock for now - would come from communications table)
        monthly_calls = workspace.voice_minutes_this_month or 0
        monthly_chats = workspace.conversations_this_month or 0
        
        result.append({
            "id": workspace.id,
            "name": workspace.name,
            "team_id": workspace.team_id,
            "owner_email": owner_query.email if owner_query else "Unknown",
            "owner_first_name": owner_query.first_name if owner_query and owner_query.first_name else "",
            "owner_last_name": owner_query.last_name if owner_query and owner_query.last_name else "",
            "owner_name": f"{owner_query.first_name or ''} {owner_query.last_name or ''}" if owner_query and (owner_query.first_name or owner_query.last_name) else (owner_query.email if owner_query else "Unknown"),
            "plan": team.plan_name if team else "Starter",
            "status": team.subscription_status if team else "active",
            "agent_count": agent_count,
            "phone_count": phone_count,
            "monthly_calls": monthly_calls,
            "monthly_chats": monthly_chats,
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
            "mrr": 0  # TODO: Calculate from Stripe subscription
        })
    
    # Sort by created_at desc
    result.sort(key=lambda x: x['created_at'] or '', reverse=True)
    
    return {"items": result, "total": len(result)}

@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get workspace details with stats, agents, and integrations (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner', 'admin', 'member']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Support lookup by Team ID (since frontend often uses team_id as generic workspace identifier)
    # Check for both old 'tm_' and new 'org_' prefixes
    if workspace_id.startswith(("tm_", "org_")):
        workspace = db.query(Workspace).filter(Workspace.team_id == workspace_id).first()
    else:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        
    if not workspace:
        # If looking up by team_id failed, it might be that the workspace doesn't exist for this team yet.
        # But for get_workspace usually we expect it to exist.
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get team
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    
    # Get owner
    owner_query = db.execute(
        text("""
            SELECT u.* FROM users u 
            JOIN team_members tm ON u.id = tm.user_id 
            WHERE tm.team_id = :team_id 
            LIMIT 1
        """),
        {"team_id": workspace.team_id}
    ).fetchone()
    
    # Get stats
    from backend.models_db import Communication, Agent, PhoneNumber, Integration
    
    # Total conversations
    total_conversations = db.query(func.count(Communication.id)).filter(
        Communication.workspace_id == workspace_id
    ).scalar() or 0
    
    # Voice usage (sum of call durations in minutes)
    voice_usage = db.query(func.sum(Communication.duration)).filter(
        Communication.workspace_id == workspace_id,
        Communication.type == 'call'
    ).scalar() or 0
    voice_usage_minutes = voice_usage // 60 if voice_usage else 0
    
    # Lifetime value (mock - would come from Stripe)
    # TODO: Calculate from Stripe subscription history
    lifetime_value = 0.0
    
    # Get agents with phone numbers
    agents = db.query(Agent).filter(
        Agent.workspace_id == workspace_id,
        Agent.is_active == True
    ).all()
    
    agents_data = []
    for agent in agents:
        phone_numbers = db.query(PhoneNumber).filter(
            PhoneNumber.agent_id == agent.id
        ).all()
        
        agents_data.append({
            "id": agent.id,
            "name": agent.name,
            "phone_numbers": [
                {
                    "number": pn.phone_number,
                    "provider": "Twilio",  # Assuming Twilio
                    "is_active": True
                }
                for pn in phone_numbers
            ]
        })
    
    # Get integrations
    integrations = db.query(Integration).filter(
        Integration.workspace_id == workspace_id
    ).all()
    
    integrations_data = [
        {
            "id": integration.id,
            "provider": integration.provider,
            "is_active": integration.is_active,
            "created_at": integration.created_at.isoformat() if integration.created_at else None
        }
        for integration in integrations
    ]
    
    # Get billing history from Stripe
    billing_history = []
    if team and team.stripe_customer_id:
        try:
            if not stripe.api_key:
                 stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
                 
            # Fetch last 5 invoices
            invoices = stripe.Invoice.list(customer=team.stripe_customer_id, limit=5)
            
            for inv in invoices.data:
                billing_history.append({
                    "date": datetime.fromtimestamp(inv.created).strftime('%m/%d/%Y'),
                    "amount": inv.amount_paid / 100 if inv.amount_paid else inv.amount_due / 100,
                    "status": "Paid" if inv.status == "paid" else ("Trial" if inv.amount_paid == 0 and inv.status == "paid" else inv.status.capitalize())
                })
        except Exception as e:
            print(f"Error fetching billing history: {e}")
    
    # Get plan details and amount from Stripe
    plan_name = team.plan_name if team else "Starter"
    plan_amount = 0
    if team and team.stripe_subscription_id:
        try:
            # Sync plan details from Stripe
            subscription = stripe.Subscription.retrieve(team.stripe_subscription_id)
            
            # Helper for robust access
            def get_val(obj, key, default=None):
                return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

            items = get_val(subscription, "items")
            data = get_val(items, "data") if items else []
            
            if data:
                price = get_val(data[0], "price")
                product_id = get_val(price, "product")
                
                # Update plan name if needed
                product = stripe.Product.retrieve(product_id)
                plan_name = get_val(product, "name")
                
                unit_amount = get_val(price, "unit_amount")
                plan_amount = unit_amount / 100 if unit_amount else 0
        except Exception as e:
            print(f"Error fetching subscription details: {e}")
            
    return {
        "id": workspace.id,
        "name": workspace.name,
        "team_id": workspace.team_id,
        "owner_email": owner_query.email if owner_query else None,
        "owner_first_name": owner_query.first_name if owner_query and owner_query.first_name else "",
        "owner_last_name": owner_query.last_name if owner_query and owner_query.last_name else "",
        "owner_name": f"{owner_query.first_name or ''} {owner_query.last_name or ''}" if owner_query and (owner_query.first_name or owner_query.last_name) else (owner_query.email if owner_query else "Unknown"),
        "plan": plan_name,
        "plan_amount": plan_amount,
        "status": team.subscription_status if team else "active",
        "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        "address": workspace.address,
        "phone": workspace.phone,
        "email": workspace.email,
        "website": workspace.website,
        "custom_agent_limit": workspace.custom_agent_limit if hasattr(workspace, 'custom_agent_limit') else None,
        "custom_call_limit": workspace.custom_call_limit if hasattr(workspace, 'custom_call_limit') else None,
        "custom_chat_limit": workspace.custom_chat_limit if hasattr(workspace, 'custom_chat_limit') else None,
        # Business Profile
        "description": workspace.description,
        "services": workspace.services,
        "business_hours": workspace.business_hours,
        "faq": workspace.faq,
        "reference_urls": workspace.reference_urls,
        # Stats
        "stats": {
            "total_conversations": total_conversations,
            "voice_usage_minutes": voice_usage_minutes,
            "lifetime_value": lifetime_value
        },
        # Agents
        "agents": agents_data,
        # Integrations
        "integrations": integrations_data,
        # Billing
        "billing_history": billing_history,
        # Limits
        "limits": {
            "agents": workspace.custom_agent_limit if getattr(workspace, 'custom_agent_limit', None) else get_plan_limits(team.plan_name if team else "Starter")['chatbots'],
            "voice_minutes": getattr(workspace, 'custom_call_limit', None) or get_plan_limits(team.plan_name if team else "Starter")['voice_minutes'],
            "conv_limit": getattr(workspace, 'custom_chat_limit', None) or get_plan_limits(team.plan_name if team else "Starter")['conversations']
        }
    }

@router.put("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    update_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Update workspace details (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Update workspace fields
    workspace.name = update_data.workspace_name
    workspace.phone = update_data.phone
    workspace.address = update_data.address
    workspace.website = update_data.website
    workspace.email = update_data.owner_email
    
    # Update Business Profile fields
    if update_data.description is not None:
        workspace.description = update_data.description
    if update_data.services is not None:
        workspace.services = update_data.services
    if update_data.business_hours is not None:
        workspace.business_hours = update_data.business_hours
    if update_data.faq is not None:
        workspace.faq = update_data.faq
    if update_data.reference_urls is not None:
        workspace.reference_urls = update_data.reference_urls
    
    # Update owner user record
    owner_query = db.execute(
        text("""
            SELECT u.id FROM users u 
            JOIN team_members tm ON u.id = tm.user_id 
            WHERE tm.team_id = :team_id 
            LIMIT 1
        """),
        {"team_id": workspace.team_id}
    ).fetchone()
    
    if owner_query:
        user = db.query(User).filter(User.id == owner_query.id).first()
        if user:
            user.first_name = update_data.owner_first_name
            user.last_name = update_data.owner_last_name
            user.email = update_data.owner_email
    
    db.commit()
    db.refresh(workspace)
    
    return {
        "success": True,
        "message": "Workspace updated successfully",
        "workspace_id": workspace_id
    }

@router.patch("/{workspace_id}/status")
def update_workspace_status(
    workspace_id: str,
    status_update: WorkspaceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Update workspace status (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get team
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Track what was done
    actions_taken = []
    stripe_status = None
    integrations_affected = 0
    agents_affected = 0
    
    # Handle Stripe subscription
    # Handle Stripe subscription
    if team.stripe_subscription_id:
        try:
            if status_update.status == 'suspended':
                # Pause the subscription
                stripe.Subscription.modify(
                    team.stripe_subscription_id,
                    pause_collection={'behavior': 'void'}
                )
                stripe_status = "paused"
                actions_taken.append("Stripe subscription paused")
            elif status_update.status == 'active':
                # Resume the subscription
                stripe.Subscription.modify(
                    team.stripe_subscription_id,
                    pause_collection=''
                )
                stripe_status = "active"
                actions_taken.append("Stripe subscription resumed")
        except Exception as e:
            print(f"Stripe error: {e}")
            actions_taken.append(f"Stripe error: {str(e)}")
    
    # Handle integrations
    from backend.models_db import Integration, Agent
    
    if status_update.status == 'suspended':
        # Deactivate all integrations
        integrations = db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.is_active == True
        ).all()
        
        for integration in integrations:
            integration.is_active = False
            integrations_affected += 1
        
        if integrations_affected > 0:
            actions_taken.append(f"{integrations_affected} integration(s) disconnected")
        
        # Deactivate all agents
        agents = db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.is_active == True
        ).all()
        
        for agent in agents:
            agent.is_active = False
            agents_affected += 1
        
        if agents_affected > 0:
            actions_taken.append(f"{agents_affected} agent(s) deactivated")
    
    elif status_update.status == 'active':
        # When reactivating, automatically enable the orchestrator agent
        orchestrator = db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.is_orchestrator == True
        ).first()
        
        if orchestrator and not orchestrator.is_active:
            orchestrator.is_active = True
            agents_affected = 1
            actions_taken.append("Orchestrator agent reactivated")
    
    # Note: When reactivating, integrations and non-orchestrator agents remain inactive
    # They must be manually reconnected/reactivated
    
    # Update team subscription status
    team.subscription_status = status_update.status
    db.commit()
    db.refresh(team)
    
    return {
        "success": True,
        "message": f"Workspace status updated to {status_update.status}",
        "workspace_id": workspace_id,
        "status": status_update.status,
        "actions_taken": actions_taken,
        "stripe_status": stripe_status,
        "integrations_affected": integrations_affected,
        "agents_affected": agents_affected
    }


# =========================================================================
# Admin Data Access Endpoints (Proxy to Workspace Services)
# =========================================================================

@router.get("/{workspace_id}/customers")
def get_workspace_customers(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customers for a specific workspace."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    service = CRMService(db)
    skip = (page - 1) * limit
    return service.get_customers(workspace.id, skip=skip, limit=limit, search=search)


@router.get("/{workspace_id}/communications")
def get_workspace_communications(
    workspace_id: str,
    search: Optional[str] = "",
    timeRange: Optional[str] = "7d",
    type: Optional[str] = None,
    channel: Optional[str] = None,
    agent_id: Optional[str] = Query(None, alias="agent"),
    direction: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get communications for a specific workspace."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")
         
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Reuse logic from communications router (inline for now as service extraction is partial)
    query = db.query(Communication).filter(Communication.workspace_id == workspace.id)

    if type and type != 'all':
        query = query.filter(Communication.type == type)
    if channel and channel != 'all':
        query = query.filter(Communication.channel == channel)
    if agent_id and agent_id != 'all':
        query = query.filter(Communication.agent_id == agent_id)
    if direction and direction != 'all':
        query = query.filter(Communication.direction == direction)
        
    # TODO: Implement timeRange filtering logic if needed strictly matching frontend
    # For now, relying on basic filters
        
    total = query.count()
    items = query.order_by(desc(Communication.started_at)).offset(offset).limit(limit).all()
    
    results = []
    for item in items:
        item_dict = {c.name: getattr(item, c.name) for c in item.__table__.columns}
        if 'transcript' not in item_dict:
            item_dict['transcript'] = None
        results.append(item_dict)
    
    return {
        "total": total,
        "items": results,
        "page": (offset // limit) + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/{workspace_id}/appointments")
def get_workspace_appointments(
    workspace_id: str,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get appointments for a specific workspace."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    query = db.query(Appointment).filter(Appointment.workspace_id == workspace.id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    total = query.count()
    items = query.order_by(desc(Appointment.appointment_date)).offset(offset).limit(limit).all()
    
    # Simple stats for the cards
    from datetime import datetime
    now = datetime.now()
    upcoming = db.query(Appointment).filter(
        Appointment.workspace_id == workspace.id, 
        Appointment.appointment_date >= now,
        Appointment.status != 'cancelled'
    ).count()
    
    completed = db.query(Appointment).filter(
        Appointment.workspace_id == workspace.id, 
        Appointment.status == 'completed'
    ).count()
    
    completion_rate = int((completed / total * 100)) if total > 0 else 0

    results = [{c.name: getattr(item, c.name) for c in item.__table__.columns} for item in items]
    
    return {
        "total": total,
        "items": results,
        "upcoming_7_days": upcoming, # Reuse key name from main endpoint
        "completion_rate": completion_rate,
        "page": (offset // limit) + 1,
        "limit": limit
    }


@router.get("/{workspace_id}/campaigns")
def get_workspace_campaigns(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get campaigns for a specific workspace."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace.id).all()
    return campaigns


@router.get("/{workspace_id}/tasks")
def get_workspace_tasks(
    workspace_id: str,
    page: int = 1,
    limit: int = 20,
    status: str = None,
    worker_type: str = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get worker tasks for a specific workspace."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    service = WorkerService(db)
    
    # WorkerService.get_tasks might expect user_id/team_id or be general. 
    # Let's check or assume we can filter by workspace_id manually or service supports it.
    # Looking at similar services, often methods take workspace_id.
    # If standard get_tasks filters by user context, we might need a specific method or manual query.
    # Let's try passing workspace_id if the service method signature supports it, 
    # otherwise we might need to query the model directly here for admin speed.
    
    # For safety/correctness given we can't see WorkerService source right now easily:
    # We'll use the service but if it requires user content, we might be limited.
    # Actually, let's query the WorkerTask model directly to be safe and independent of user context.
    from backend.models_db import WorkerTask
    
    query = db.query(WorkerTask).filter(WorkerTask.workspace_id == workspace.id)
    
    if status and status != 'all':
        query = query.filter(WorkerTask.status == status)
    if worker_type and worker_type != 'all':
        query = query.filter(WorkerTask.worker_type == worker_type)
        
    total = query.count()
    offset = (page - 1) * limit
    tasks = query.order_by(desc(WorkerTask.created_at)).offset(offset).limit(limit).all()
    
    return {
        "tasks": tasks,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/{workspace_id}/analytics/summary")
def get_workspace_analytics_summary(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get analytics summary for a specific workspace (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        return {
            "total_conversations": 0, "avg_duration": 0.0, "successful_conversations": 0,
            "total_minutes": 0.0, "total_agents": 0, "total_messages": 0,
            "minutes_limit": 100, "agents_limit": 1, "conversations_limit": 1000
        }
    
    # Replicate logic from analytics.py
    from sqlalchemy import func, case, or_
    from backend.models_db import Communication, Agent
    from backend.subscription_limits import get_plan_limits
    from backend.models_db import Team
    
    # Get plan limits
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    plan_name = team.plan_name if team else "Starter"
    limits = get_plan_limits(plan_name)
    
    # Define positive outcomes
    POSITIVE_OUTCOMES = ['Information Provided', 'Appointment Booked', 'Resolved', 
                         'Appointment Rescheduled', 'Follow-up Needed']
    positive_outcome_conditions = or_(
        *[Communication.call_outcome.ilike(f'%{outcome}%') for outcome in POSITIVE_OUTCOMES]
    )
    
    query = db.query(
        func.count(Communication.id),
        func.avg(Communication.duration),
        func.sum(case((Communication.status == "completed", 1), else_=0)),
        func.sum(Communication.duration)
    ).filter(
        Communication.workspace_id == workspace.id
    )
    
    result = query.first()
    
    total = result[0] or 0
    avg_duration = result[1] or 0.0
    
    successful_query = db.query(func.count(Communication.id)).filter(
        Communication.workspace_id == workspace.id,
        Communication.status == "completed",
        positive_outcome_conditions
    )
    successful = successful_query.scalar() or 0
    
    total_minutes = workspace.voice_minutes_this_month or 0
    
    total_agents = db.query(func.count(Agent.id)).filter(
        Agent.workspace_id == workspace.id
    ).scalar() or 0
    
    total_messages = db.query(func.count(Communication.id)).filter(
        Communication.workspace_id == workspace.id,
        Communication.type == "chat"
    ).scalar() or 0
    
    return {
        "total_conversations": total,
        "avg_duration": float(avg_duration),
        "successful_conversations": successful,
        "total_minutes": round(float(total_minutes), 1),
        "total_agents": total_agents,
        "total_messages": total_messages,
        "minutes_limit": limits["voice_minutes"],
        "agents_limit": limits["chatbots"],
        "conversations_limit": limits["conversations"]
    }

    return {
        "total_conversations": total,
        "avg_duration": float(avg_duration),
        "successful_conversations": successful,
        "total_minutes": round(float(total_minutes), 1),
        "total_agents": total_agents,
        "total_messages": total_messages,
        "minutes_limit": limits["voice_minutes"],
        "agents_limit": limits["chatbots"],
        "conversations_limit": limits["conversations"]
    }


@router.get("/{workspace_id}/billing/stats")
def get_workspace_billing_stats(
    workspace_id: str,
    time_range: int = 30,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get billing statistics for a specific workspace (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    if not team or not team.stripe_customer_id:
        # Return empty stats if no stripe customer
        return {
            "total_revenue": 0,
            "revenue_change": 0,
            "active_subscribers": 0 if team.subscription_status != 'active' else 1,
            "subscriber_change": 0,
            "pending_amount": 0,
            "pending_count": 0,
            "failed_payments": 0
        }

    from datetime import datetime, timedelta
    
    if not stripe.api_key:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range)
    
    try:
        # Get invoices for this customer in this time period
        invoices = stripe.Invoice.list(
            customer=team.stripe_customer_id,
            limit=100,
            created={
                'gte': int(start_date.timestamp()),
                'lte': int(end_date.timestamp())
            }
        )
        
        # Calculate stats
        total_revenue = sum(inv.amount_paid / 100 for inv in invoices.data if inv.status == 'paid')
        pending_amount = sum(inv.amount_due / 100 for inv in invoices.data if inv.status == 'open')
        pending_count = len([inv for inv in invoices.data if inv.status == 'open'])
        failed_payments = len([inv for inv in invoices.data if inv.status == 'uncollectible'])
        
        # Calculate revenue change
        prev_start = start_date - timedelta(days=time_range)
        prev_invoices = stripe.Invoice.list(
            customer=team.stripe_customer_id,
            limit=100,
            created={
                'gte': int(prev_start.timestamp()),
                'lte': int(start_date.timestamp())
            }
        )
        prev_revenue = sum(inv.amount_paid / 100 for inv in prev_invoices.data if inv.status == 'paid')
        revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "revenue_change": round(revenue_change, 1),
            "active_subscribers": 1 if team.subscription_status == 'active' else 0,
            "subscriber_change": 0, # Not relevant for single workspace
            "pending_amount": pending_amount,
            "pending_count": pending_count,
            "failed_payments": failed_payments
        }
    except Exception as e:
        print(f"Stripe stats error: {e}")
        return {
            "total_revenue": 0, "revenue_change": 0, "active_subscribers": 0,
            "subscriber_change": 0, "pending_amount": 0, "pending_count": 0, "failed_payments": 0
        }


@router.get("/{workspace_id}/billing/invoices")
def get_workspace_invoices(
    workspace_id: str,
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get invoices for a specific workspace (admin only)."""
    if current_user.role not in ['supaagent_admin', 'owner']:
         raise HTTPException(status_code=403, detail="Admin access required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    if not team or not team.stripe_customer_id:
        return {"invoices": [], "total": 0, "has_more": False}

    from datetime import datetime
    import stripe
    import os
    
    try:
        # Get invoices from Stripe
        params = {
            'customer': team.stripe_customer_id,
            'limit': limit
        }
        if status and status != 'all':
            params['status'] = status
            
        params['limit'] = limit # Verify limit is passed
             
        print(f"DEBUG INVOICES: Fetching for customer {team.stripe_customer_id} with params {params} (Team ID: {team.id})")
        invoices = stripe.Invoice.list(**params)
        print(f"DEBUG INVOICES: Found {len(invoices.data)} invoices")
        
        invoice_list = []
        for inv in invoices.data:
        # Map Stripe status
            status_map = {
                'paid': 'paid',
                'open': 'pending',
                'uncollectible': 'failed',
                'void': 'refunded'
            }
            
            invoice_list.append({
                "id": inv.id,
                "invoice_number": inv.number or f"#INV-{inv.id[:8]}",
                "customer_name": workspace.name or "Unknown", # Use workspace name
                "plan": f"Invoice", # specific plan name hard to get efficiently without expanding
                "date": datetime.fromtimestamp(inv.created).strftime('%b %d, %Y'),
                "amount": inv.amount_paid / 100 if inv.amount_paid else inv.amount_due / 100,
                "status": status_map.get(inv.status, inv.status),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url
            })
            
        return {
            "invoices": invoice_list,
            "total": len(invoice_list),
            "has_more": invoices.has_more
        }
    except Exception as e:
        print(f"Stripe invoices error: {e}")
        return {"invoices": [], "total": 0, "has_more": False}
