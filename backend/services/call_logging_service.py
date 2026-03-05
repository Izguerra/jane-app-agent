"""
Call Logging Service

Logs call details to the communications table and updates related records.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models_db import Communication, Appointment, Deal, Customer, AppointmentReminder
from datetime import datetime


class CallLoggingService:
    @staticmethod
    def log_call_start(
        communication_id: str,
        workspace_id: str,
        to_phone: str,
        call_intent: str,
        call_context: Dict[str, Any],
        customer_id: Optional[str],
        agent_id: Optional[str],
        twilio_call_sid: str,
        campaign_id: Optional[str],
        campaign_name: Optional[str],
        db: Session
    ) -> Communication:
        """Log the start of an outbound call"""
        communication = Communication(
            id=communication_id,
            workspace_id=workspace_id,
            type="call",
            direction="outbound",
            status="initiated",
            user_identifier=to_phone,
            channel="phone_call",
            agent_id=agent_id,
            call_intent=call_intent,
            call_context=call_context,
            customer_id=customer_id,
            twilio_call_sid=twilio_call_sid,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            started_at=datetime.utcnow()
        )
        db.add(communication)
        db.commit()
        db.refresh(communication)
        return communication
    
    @staticmethod
    def update_call_status(
        communication_id: str,
        status: str,
        call_outcome: Optional[str],
        transcript: Optional[str],
        summary: Optional[str],
        sentiment: Optional[str],
        recording_url: Optional[str],
        duration: Optional[int],
        db: Session
    ) -> Optional[Communication]:
        """Update call status and details"""
        communication = db.query(Communication).filter(
            Communication.id == communication_id
        ).first()
        
        if not communication:
            return None
        
        communication.status = status
        if call_outcome:
            communication.call_outcome = call_outcome
        if transcript:
            communication.transcript = transcript
        if summary:
            communication.summary = summary
        if sentiment:
            communication.sentiment = sentiment
        if recording_url:
            communication.recording_url = recording_url
        if duration is not None:
            communication.duration = duration
        
        if status in ["completed", "failed", "no-answer", "busy"]:
            communication.ended_at = datetime.utcnow()
        
        db.commit()
        db.refresh(communication)
        return communication
    
    @staticmethod
    def process_call_outcome(
        communication_id: str,
        call_outcome: str,
        db: Session
    ):
        """Process call outcome and update related records"""
        communication = db.query(Communication).filter(
            Communication.id == communication_id
        ).first()
        
        if not communication:
            return
        
        call_context = communication.call_context or {}
        call_intent = communication.call_intent
        
        # Update appointment status if this was a reminder call
        if call_intent == "appointment_reminder" and "appointment" in call_context:
            appointment_id = call_context["appointment"].get("id")
            if appointment_id:
                appointment = db.query(Appointment).filter(
                    Appointment.id == appointment_id
                ).first()
                
                if appointment and call_outcome == "answered":
                    appointment.status = "confirmed"
                    db.commit()
                
                # Update reminder status
                reminder = db.query(AppointmentReminder).filter(
                    AppointmentReminder.appointment_id == appointment_id,
                    AppointmentReminder.communication_id == communication_id
                ).first()
                
                if reminder:
                    reminder.status = "sent" if call_outcome == "answered" else "failed"
                    db.commit()
        
        # Update deal last contact date if this was a follow-up call
        elif call_intent == "deal_follow_up" and "deal" in call_context:
            deal_id = call_context["deal"].get("id")
            if deal_id and call_outcome == "answered":
                deal = db.query(Deal).filter(
                    Deal.id == deal_id
                ).first()
                
                if deal:
                    deal.last_contact_date = datetime.utcnow()
                    db.commit()
        
        # Update customer last contact date
        if communication.customer_id and call_outcome == "answered":
            customer = db.query(Customer).filter(
                Customer.id == communication.customer_id
            ).first()
            
            if customer:
                customer.last_contact_date = datetime.utcnow()
                db.commit()


# Singleton instance
call_logging_service = CallLoggingService()
