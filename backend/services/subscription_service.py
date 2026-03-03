
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.models_db import Subscription, SubscriptionUsage, Workspace
from backend.lib.id_service import IdService
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_subscription(self, workspace_id: str) -> Subscription:
        sub = self.db.query(Subscription).filter(Subscription.workspace_id == workspace_id).first()
        if not sub:
            # Auto-create starter subscription if missing
            return self.create_subscription(workspace_id)
        return sub

    def create_subscription(self, workspace_id: str, tier: str = "starter") -> Subscription:
        sub_id = IdService.generate("sub")
        new_sub = Subscription(
            id=sub_id,
            workspace_id=workspace_id,
            tier=tier,
            status="active",
            billing_period_start=datetime.utcnow()
            # billing_period_end logic will come from Stripe or fixed 30 days
        )
        self.db.add(new_sub)
        self.db.commit()
        self.db.refresh(new_sub)
        return new_sub

    def get_usage(self, workspace_id: str) -> SubscriptionUsage:
        current_cycle = datetime.utcnow().strftime("%Y-%m")
        usage = self.db.query(SubscriptionUsage).filter(
            SubscriptionUsage.workspace_id == workspace_id,
            SubscriptionUsage.billing_cycle_key == current_cycle
        ).first()
        
        if not usage:
            usage_id = IdService.generate("usage")
            usage = SubscriptionUsage(
                id=usage_id,
                workspace_id=workspace_id,
                billing_cycle_key=current_cycle,
            )
            self.db.add(usage)
            # Commit first to ensure object exists before syncing
            self.db.commit()
            self.db.refresh(usage)
            
        # Dynamic Entitlement Check:
        # Always check if the current plan limits differ from the stored usage limits.
        # This ensures that if we update the plan definition in code, users see it immediately.
        sub = self.get_subscription(workspace_id)
        limits = self._get_tier_limits(sub.tier)
        
        limits_changed = False
        if usage.voice_minutes_limit != limits["voice_minutes"]:
            usage.voice_minutes_limit = limits["voice_minutes"]
            limits_changed = True
            
        if usage.sms_limit != limits["sms"]:
            usage.sms_limit = limits["sms"]
            limits_changed = True
            
        if usage.whatsapp_limit != limits["whatsapp"]:
            usage.whatsapp_limit = limits["whatsapp"]
            limits_changed = True
            
        # Check if chatbot_limit exists on usage model (it should based on schema)
        if hasattr(usage, 'chatbot_limit') and usage.chatbot_limit != limits.get("chatbots", 1):
             usage.chatbot_limit = limits.get("chatbots", 1)
             limits_changed = True

        if limits_changed:
            self.db.commit()
            self.db.refresh(usage)
            
        return usage

    def _get_tier_limits(self, tier: str) -> dict:
        from backend.subscription_limits import get_plan_limits
        return get_plan_limits(tier)

    def track_usage(self, workspace_id: str, metric: str, amount: float = 1):
        usage = self.get_usage(workspace_id)
        
        if metric == "voice_minutes":
            usage.voice_minutes_used += amount # Float addition
        elif metric == "sms":
            usage.sms_sent += int(amount)
        elif metric == "whatsapp":
            usage.whatsapp_sent += int(amount)
        elif metric == "chatbot":
            usage.chatbot_turns += int(amount)
            
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def sync_usage_from_history(self, workspace_id: str):
        """
        Calculates usage from raw Communication logs for the current month 
        and updates the SubscriptionUsage record. usage self-healing.
        """
        from backend.models_db import Communication
        from sqlalchemy import and_
        
        # 1. Get usage record + Billing cycle dates
        usage = self.get_usage(workspace_id)
        # Assuming current billing cycle is effectively "Start of this Month" for now
        # Ideally, we read 'billing_period_start' from Subscription table
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        # 2. Aggregate from History
        # Voice Metrics
        voice_stats = self.db.query(
            func.sum(Communication.duration)
        ).filter(
            Communication.workspace_id == workspace_id,
            Communication.type == "call",
            Communication.started_at >= start_of_month
        ).scalar()
        
        total_voice_seconds = voice_stats or 0
        total_voice_minutes = total_voice_seconds / 60.0
        
        # SMS Metrics (including 'whatsapp' if we treated them as channels)
        sms_count = self.db.query(func.count(Communication.id)).filter(
            Communication.workspace_id == workspace_id,
            Communication.channel == "sms",
            Communication.direction == "outbound",
            Communication.started_at >= start_of_month
        ).scalar() or 0
        
        whatsapp_count = self.db.query(func.count(Communication.id)).filter(
            Communication.workspace_id == workspace_id,
            Communication.channel == "whatsapp",
            Communication.direction == "outbound",
            Communication.started_at >= start_of_month
        ).scalar() or 0
        
        # 3. Update Usage Record
        # Only update if our tracked usage is suspiciously low (or just overwrite to be safe)
        # For self-healing, overwriting is safer to ensure consistency.
        
        usage.voice_minutes_used = total_voice_minutes
        usage.sms_sent = sms_count
        usage.whatsapp_sent = whatsapp_count
        # usage.chatbot_turns # Harder to derive from history unless looking at messages count
        
        self.db.commit()
        self.db.refresh(usage)
        return usage
