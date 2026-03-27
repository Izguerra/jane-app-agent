from sqlalchemy.orm import Session
from backend.services.crm_customer_ops import CRMCustomerOps
from backend.services.crm_analytics_service import CRMAnalyticsService
from backend.services.crm_interaction_service import CRMInteractionService

class CRMService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, workspace_id: str, agent_id: str = None):
        return CRMAnalyticsService.get_dashboard_stats(self.db, workspace_id, agent_id)

    def get_recent_activity(self, workspace_id: str, limit: int = 5, agent_id: str = None):
        return CRMAnalyticsService.get_recent_activity(self.db, workspace_id, limit, agent_id)

    def get_customers(self, workspace_id: str, skip: int = 0, limit: int = 10, search: str = None):
        from sqlalchemy import desc
        from backend.models_db import Customer
        query = self.db.query(Customer).filter(Customer.workspace_id == workspace_id, Customer.status.notin_(['converted', 'deleted']))
        if search:
            s_filt = f"%{search}%"
            query = query.filter((Customer.first_name.ilike(s_filt)) | (Customer.last_name.ilike(s_filt)) | (Customer.email.ilike(s_filt)))
        return {"items": query.order_by(desc(Customer.created_at)).offset(skip).limit(limit).all(), "total": query.count()}

    def create_customer(self, workspace_id: str, data: dict):
        return CRMCustomerOps.create_customer(self.db, workspace_id, data)

    def get_customer_by_id(self, workspace_id: str, customer_id: str):
        from backend.models_db import Customer
        return self.db.query(Customer).filter(Customer.id == customer_id, Customer.workspace_id == workspace_id).first()

    def get_customer_communications(self, customer_id: str, limit: int = 10, offset: int = 0, type: str = None):
        return CRMInteractionService.get_customer_communications(self.db, customer_id, limit, offset, type)

    def get_customer_analytics(self, customer_id: str, workspace_id: str, period_type: str = "month", period_value: str = None):
        return CRMAnalyticsService.get_customer_analytics(self.db, customer_id, workspace_id, period_type, period_value)

    def analyze_and_update_customer_status(self, customer_id: str, interaction_text: str, interaction_type: str = "chat"):
        import asyncio
        return asyncio.run(CRMInteractionService.analyze_and_update_status(self.db, customer_id, interaction_text, interaction_type))

    def get_or_create_from_identifier(self, workspace_id: str, identifier: str, channel: str = "phone", name: str = None):
        return CRMCustomerOps.get_or_create_from_identifier(self.db, workspace_id, identifier, channel, name)

    def convert_to_customer(self, customer_id: str, conversion_trigger: str):
        return CRMCustomerOps.convert_to_customer(self.db, customer_id, conversion_trigger)

    def ensure_customer_from_interaction(self, workspace_id: str, identifier: str, channel: str, name: str = None):
        from datetime import datetime, timezone
        customer = self.get_or_create_from_identifier(workspace_id, identifier, channel, name)
        if customer:
            customer.last_contact_date = datetime.now(timezone.utc)
            self.db.commit()
        return customer

    def cleanup_stale_sessions(self, workspace_id: str, minutes_timeout: int = 5):
        from datetime import datetime, timezone, timedelta
        from backend.models_db import Communication
        
        limit = datetime.now(timezone.utc) - timedelta(minutes=minutes_timeout)
        
        stale_comms = self.db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.status == "ongoing",
            Communication.started_at < limit
        ).all()
        
        for comm in stale_comms:
            comm.status = "completed"
            comm.call_outcome = "Session Timeout (Auto)"
            comm.ended_at = datetime.now(timezone.utc)
        
        if stale_comms:
            self.db.commit()

    def get_customer_appointments(self, customer_id: str, limit: int = 10, offset: int = 0):
        return CRMInteractionService.get_customer_appointments(self.db, customer_id, limit, offset)

    def get_customer_campaigns(self, customer_id: str, limit: int = 10, offset: int = 0):
        from backend.models_db import CampaignEnrollment
        query = self.db.query(CampaignEnrollment).filter(CampaignEnrollment.customer_id == customer_id).order_by(CampaignEnrollment.created_at.desc())
        return {"items": query.offset(offset).limit(limit).all(), "total": query.count()}

    def get_customer_voice_calls(self, customer_id: str, limit: int = 20, offset: int = 0):
        from backend.models_db import Communication
        query = self.db.query(Communication).filter(Communication.customer_id == customer_id, Communication.type == 'call').order_by(Communication.started_at.desc())
        return {"items": query.offset(offset).limit(limit).all(), "total": query.count()}

def run_session_cleanup(workspace_id: str):
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        service = CRMService(db)
        service.cleanup_stale_sessions(workspace_id)
    finally:
        db.close()
