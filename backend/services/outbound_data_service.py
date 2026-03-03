"""
Outbound Data Service

Fetches customer, appointment, and deal data for call context.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models_db import Customer, Appointment, Deal
from datetime import datetime


class OutboundDataService:
    @staticmethod
    def get_customer_data(customer_id: str, workspace_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Get customer data for call context"""
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id
        ).first()
        
        if not customer:
            return None
        
        return {
            "id": customer.id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "full_name": f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
            "email": customer.email,
            "phone": customer.phone,
            "company_name": customer.company_name,
            "status": customer.status,
            "plan": customer.plan,
            "lead_source": customer.lead_source,
            "tags": customer.tags
        }
    
    @staticmethod
    def get_appointment_data(appointment_id: str, workspace_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Get appointment data for call context"""
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.workspace_id == workspace_id
        ).first()
        
        if not appointment:
            return None
        
        # Get customer data
        customer_data = None
        if appointment.customer_id:
            customer_data = OutboundDataService.get_customer_data(
                appointment.customer_id,
                workspace_id,
                db
            )
        
        return {
            "id": appointment.id,
            "title": appointment.title,
            "description": appointment.description,
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            "duration_minutes": appointment.duration_minutes,
            "status": appointment.status,
            "location": appointment.location,
            "notes": appointment.notes,
            "customer": customer_data
        }
    
    @staticmethod
    def get_deal_data(deal_id: str, workspace_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Get deal data for call context"""
        deal = db.query(Deal).filter(
            Deal.id == deal_id,
            Deal.workspace_id == workspace_id
        ).first()
        
        if not deal:
            return None
        
        # Get customer data
        customer_data = None
        if deal.customer_id:
            customer_data = OutboundDataService.get_customer_data(
                deal.customer_id,
                workspace_id,
                db
            )
        
        return {
            "id": deal.id,
            "title": deal.title,
            "description": deal.description,
            "value": deal.value,
            "stage": deal.stage,
            "probability": deal.probability,
            "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
            "source": deal.source,
            "assigned_to": deal.assigned_to,
            "notes": deal.notes,
            "last_contact_date": deal.last_contact_date.isoformat() if deal.last_contact_date else None,
            "next_follow_up_date": deal.next_follow_up_date.isoformat() if deal.next_follow_up_date else None,
            "customer": customer_data
        }
    
    @staticmethod
    def build_call_context(
        call_intent: str,
        workspace_id: str,
        db: Session,
        appointment_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive call context based on intent
        
        Args:
            call_intent: Intent of the call
            workspace_id: Workspace ID
            db: Database session
            appointment_id: Appointment ID (for appointment_reminder intent)
            deal_id: Deal ID (for deal_follow_up intent)
            customer_id: Customer ID (for lead_qualification or general calls)
        
        Returns:
            Dict with call context data
        """
        context = {
            "intent": call_intent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if call_intent == "appointment_reminder" and appointment_id:
            appointment_data = OutboundDataService.get_appointment_data(
                appointment_id,
                workspace_id,
                db
            )
            if appointment_data:
                context["appointment"] = appointment_data
                context["customer"] = appointment_data.get("customer")
        
        elif call_intent == "deal_follow_up" and deal_id:
            deal_data = OutboundDataService.get_deal_data(
                deal_id,
                workspace_id,
                db
            )
            if deal_data:
                context["deal"] = deal_data
                context["customer"] = deal_data.get("customer")
        
        elif call_intent == "lead_qualification" and customer_id:
            customer_data = OutboundDataService.get_customer_data(
                customer_id,
                workspace_id,
                db
            )
            if customer_data:
                context["customer"] = customer_data
        
        elif customer_id:
            # General call with customer context
            customer_data = OutboundDataService.get_customer_data(
                customer_id,
                workspace_id,
                db
            )
            if customer_data:
                context["customer"] = customer_data
        
        return context


# Singleton instance
outbound_data_service = OutboundDataService()
