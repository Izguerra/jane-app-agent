import logging
import json
from sqlalchemy import desc
from sqlalchemy.orm import Session
from backend.models_db import Customer, Communication, Appointment, Campaign, CampaignEnrollment

logger = logging.getLogger("crm-interaction-service")

class CRMInteractionService:
    @staticmethod
    def get_customer_communications(db: Session, customer_id: str, limit: int = 10, offset: int = 0, comm_type: str = None):
        query = db.query(Communication).filter(Communication.workspace_id.in_(db.query(Customer.workspace_id).filter(Customer.id == customer_id)))
        if comm_type:
            query = query.filter(Communication.type == ('call' if comm_type == 'voice' else comm_type))
        query = query.order_by(desc(Communication.started_at))
        return {"items": query.offset(offset).limit(limit).all(), "total": query.count()}

    @staticmethod
    def get_customer_appointments(db: Session, customer_id: str, limit: int = 10, offset: int = 0):
        query = db.query(Appointment).filter(Appointment.customer_id == customer_id).order_by(desc(Appointment.appointment_date))
        return {"items": query.offset(offset).limit(limit).all(), "total": query.count()}

    @staticmethod
    async def analyze_and_update_status(db: Session, customer_id: str, interaction_text: str, interaction_type: str = "chat"):
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer: return {"success": False, "error": "Customer not found"}

        prompt = f"""Analyze interaction and return JSON with keys: "lifecycle_stage", "crm_status", "customer_type".
        Interaction: "{interaction_text}"
        Current: {customer.lifecycle_stage}, {customer.crm_status}"""
        
        try:
            from backend.lib.ai_client import get_ai_client
            client, model = get_ai_client(workspace_id=customer.workspace_id, async_mode=True)
            response = await client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}], 
                response_format={"type": "json_object"}, temperature=0.1
            )
            result = json.loads(response.choices[0].message.content)
            
            updated = False
            for field in ["lifecycle_stage", "crm_status", "customer_type"]:
                val = result.get(field)
                if val and val.lower() != (getattr(customer, field) or "").lower():
                    setattr(customer, field, val.lower())
                    updated = True
            if updated: db.commit()
            return {"success": True, "changed": updated, "analysis": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
