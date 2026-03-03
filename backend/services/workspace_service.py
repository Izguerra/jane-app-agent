from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime, timezone

from backend.models_db import (
    Workspace, Team, User, Agent, PhoneNumber, Integration, PlatformIntegration
)
from backend.services.crm_analytics_service import CRMAnalyticsService
from backend.services.billing import BillingService
from backend.subscription_limits import (
    get_plan_limits, get_available_integrations, INTEGRATION_REGISTRY
)

logger = logging.getLogger("workspace-service")

class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db
        self.billing_service = BillingService()
        self.crm_service = CRMAnalyticsService(db)

    def get_workspace_features(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get workspace features, limits, and integration status.
        """
        # Resolve workspace
        workspace = self._resolve_workspace(workspace_id)
        if not workspace:
            return None

        # Get team for plan and status
        team = self.db.query(Team).filter(Team.id == workspace.team_id).first()
        tier = (team.plan_name or "Starter").lower()
        if tier == "professional": tier = "pro"
        status = team.subscription_status or "active"

        # Get trial info from BillingService
        trial_info = {}
        if team.stripe_subscription_id:
            trial_info = self.billing_service.get_subscription_trial_status(team.stripe_subscription_id)

        # Get plan limits & integrations
        limits = get_plan_limits(tier)
        
        # Available integrations for this plan
        available_integrations = get_available_integrations(tier)
        
        # Connected integrations
        connected_integrations = self.db.query(Integration).filter(
            Integration.workspace_id == workspace.id,
            Integration.is_active == True
        ).all()
        connected_providers = [i.provider for i in connected_integrations]
        
        # Calendar logic
        calendar_providers = ["google_calendar", "exchange"]
        calendar_count = len([p for p in connected_providers if p in calendar_providers])
        calendar_limit = limits.get("max_calendar_integrations", 1)
        has_calendar = calendar_count > 0

        # Admin enabled keys
        db_enabled = self.db.query(PlatformIntegration.provider).filter(PlatformIntegration.is_enabled == True).all()
        enabled_providers_set = {row[0] for row in db_enabled}

        # Build integration details
        integration_details = []
        for provider, info in INTEGRATION_REGISTRY.items():
            is_globally_enabled = provider in enabled_providers_set
            is_connected = provider in connected_providers
            
            if not is_globally_enabled and not is_connected:
                continue
                
            is_available = provider in available_integrations
            is_calendar = info["category"] == "calendar"
            
            # Usage stats (e.g. phone numbers)
            usage_str = None
            if provider in ["phone", "twilio"]:
                 phone_count = self.db.query(func.count(PhoneNumber.id)).filter(
                    PhoneNumber.workspace_id == workspace.id
                 ).scalar() or 0
                 limit = limits.get("included_numbers", 0)
                 usage_str = f"{phone_count}/{limit} used"

            integration_details.append({
                "provider": provider,
                "display_name": info["display_name"],
                "category": info["category"],
                "available": is_available,
                "connected": is_connected,
                "disabled": is_calendar and calendar_count >= calendar_limit and not is_connected,
                "requires_upgrade": not is_available,
                "usage": usage_str
            })

        return {
            "workspace_id": workspace.id,
            "tier": tier,
            "status": status,
            "trial_end_date": trial_info.get("trial_end_date"),
            "is_trial_expired": trial_info.get("is_trial_expired", False),
            "days_until_trial_end": trial_info.get("days_until_trial_end"),
            "features": {
                "campaigns": limits.get("campaigns", False),
                "appointments": has_calendar,
                "deals": True,
                "analytics": limits.get("analytics", "basic"),
                "knowledge_base": tier != "starter"
            },
            "integrations": {
                "available": available_integrations,
                "connected": connected_providers,
                "calendar_limit": calendar_limit,
                "calendar_count": calendar_count,
                "details": integration_details
            }
        }

    def get_workspace_details(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get full workspace details for Dashboard (Stats, Agents, Billing).
        """
        workspace = self._resolve_workspace(workspace_id)
        if not workspace:
            return None
            
        team = self.db.query(Team).filter(Team.id == workspace.team_id).first()
        
        # Owner Info
        owner_query = self._get_owner_info(workspace.team_id)
        
        # Stats
        usage_stats = self.crm_service.get_workspace_usage_stats(workspace.id)
        
        # Billing History & LTV
        billing_history = []
        lifetime_value = 0.0
        
        if team.stripe_customer_id:
            billing_history = self.billing_service.get_billing_history(team.stripe_customer_id)
            lifetime_value = self.billing_service.calculate_ltv(team.stripe_customer_id)
            
        # Agents & Phone Numbers
        agents_data = self._get_agents_data(workspace.id)
        
        # Integrations
        integrations_data = self._get_integrations_data(workspace.id)
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "team_id": workspace.team_id,
            "owner_email": owner_query.email if owner_query else None,
            "owner_first_name": owner_query.first_name if owner_query else "",
            "owner_last_name": owner_query.last_name if owner_query else "",
            "owner_name": self._format_owner_name(owner_query),
            "plan": team.plan_name if team else "Starter",
            "status": team.subscription_status if team else "active",
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
            # Profile Fields
            "address": workspace.address,
            "phone": workspace.phone,
            "email": workspace.email,
            "website": workspace.website,
            "description": workspace.description,
            "services": workspace.services,
            "business_hours": workspace.business_hours,
            "faq": workspace.faq,
            "reference_urls": workspace.reference_urls,
            # Aggregated Data
            "stats": {
                "total_conversations": usage_stats["conversations_count"],
                "voice_usage_minutes": usage_stats["voice_minutes_used"],
                "lifetime_value": lifetime_value
            },
            "agents": agents_data,
            "integrations": integrations_data,
            "billing_history": billing_history
        }

    def update_workspace_status(self, workspace_id: str, new_status: str) -> Dict[str, Any]:
        """
        Handle workspace status changes (Active/Suspended), affecting Stripe & Integrations.
        """
        workspace = self._resolve_workspace(workspace_id)
        if not workspace:
            return None
            
        team = self.db.query(Team).filter(Team.id == workspace.team_id).first()
        if not team:
            raise ValueError("Team not found")

        actions_taken = []
        stripe_status = None
        integrations_affected = 0
        agents_affected = 0

        # Stripe Subscription
        if team.stripe_subscription_id:
            try:
                if new_status == 'suspended':
                    self.billing_service.pause_subscription(team.stripe_subscription_id)
                    stripe_status = "paused"
                    actions_taken.append("Stripe subscription paused")
                elif new_status == 'active':
                    self.billing_service.resume_subscription(team.stripe_subscription_id)
                    stripe_status = "active"
                    actions_taken.append("Stripe subscription resumed")
            except Exception as e:
                actions_taken.append(f"Stripe error: {str(e)}")

        # Integrations & Agents
        if new_status == 'suspended':
            # Deactivate Integrations
            integrations = self.db.query(Integration).filter(
                Integration.workspace_id == workspace.id,
                Integration.is_active == True
            ).all()
            for integration in integrations:
                integration.is_active = False
                integrations_affected += 1
            if integrations_affected > 0:
                actions_taken.append(f"{integrations_affected} integration(s) disconnected")

            # Deactivate Agents
            agents = self.db.query(Agent).filter(
                Agent.workspace_id == workspace.id,
                Agent.is_active == True
            ).all()
            for agent in agents:
                agent.is_active = False
                agents_affected += 1
            if agents_affected > 0:
                actions_taken.append(f"{agents_affected} agent(s) deactivated")

        elif new_status == 'active':
            # Reactivate Orchestrator
            orchestrator = self.db.query(Agent).filter(
                Agent.workspace_id == workspace.id,
                Agent.is_orchestrator == True
            ).first()
            if orchestrator and not orchestrator.is_active:
                orchestrator.is_active = True
                agents_affected = 1
                actions_taken.append("Orchestrator agent reactivated")

        # Update DB
        team.subscription_status = new_status
        self.db.commit()
        self.db.refresh(team)

        return {
            "success": True,
            "message": f"Workspace status updated to {new_status}",
            "workspace_id": workspace.id,
            "status": new_status,
            "actions_taken": actions_taken,
            "stripe_status": stripe_status,
            "integrations_affected": integrations_affected,
            "agents_affected": agents_affected
        }

    # --- Helper Private Methods ---

    def _resolve_workspace(self, workspace_id: str) -> Optional[Workspace]:
        if workspace_id.startswith(("tm_", "org_")):
            return self.db.query(Workspace).filter(Workspace.team_id == workspace_id).first()
        return self.db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def _get_owner_info(self, team_id: str):
        return self.db.execute(
            text("""
                SELECT u.* FROM users u 
                JOIN team_members tm ON u.id = tm.user_id 
                WHERE tm.team_id = :team_id 
                LIMIT 1
            """),
            {"team_id": team_id}
        ).fetchone()

    def _format_owner_name(self, owner_query) -> str:
        if not owner_query:
            return "Unknown"
        if owner_query.first_name or owner_query.last_name:
            return f"{owner_query.first_name or ''} {owner_query.last_name or ''}".strip()
        return owner_query.email

    def _get_agents_data(self, workspace_id: str) -> List[Dict]:
        agents = self.db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.is_active == True
        ).all()
        
        result = []
        for agent in agents:
            phone_numbers = self.db.query(PhoneNumber).filter(
                PhoneNumber.agent_id == agent.id
            ).all()
            result.append({
                "id": agent.id,
                "name": agent.name,
                "phone_numbers": [
                    {"number": pn.phone_number, "provider": "Twilio", "is_active": True}
                    for pn in phone_numbers
                ]
            })
        return result

    def _get_integrations_data(self, workspace_id: str) -> List[Dict]:
        integrations = self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id
        ).all()
        return [
            {
                "id": i.id,
                "provider": i.provider,
                "is_active": i.is_active,
                "created_at": i.created_at.isoformat() if i.created_at else None
            }
            for i in integrations
        ]
