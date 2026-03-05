from sqlalchemy.orm import Session
from backend.models_db import Communication, Customer, Appointment, Deal, CampaignEnrollment, Campaign
from sqlalchemy import desc, func
from typing import List, Dict, Any
import json

class CustomerHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_recent_communications(self, customer_id: str, limit: int = 5) -> List[Communication]:
        """
        Fetch recent communications for a customer across all channels.
        """
        return self.db.query(Communication).filter(
            Communication.customer_id == customer_id
        ).order_by(desc(Communication.started_at)).limit(limit).all()

    def get_customer_context(self, customer_id: str, limit: int = 5) -> str:
        """
        Build a text-based context summary of the customer's history.
        This is injected into the Agent's system prompt.
        """
        try:
            # 1. Fetch Basic Customer Info
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return ""

            context_parts = []
            
            # IDENTITY
            name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or "Unknown"
            context_parts.append(f"CUSTOMER CONTEXT:\nName: {name}")
            if customer.email: context_parts.append(f"Email: {customer.email}")
            if customer.phone: context_parts.append(f"Phone: {customer.phone}")
            if customer.company_name: context_parts.append(f"Company: {customer.company_name}")
            
            # STATUS
            context_parts.append(f"Status: {customer.status} ({customer.customer_type})")
            
            # 2. Recent Interactions (The "Memory")
            comms = self.get_recent_communications(customer_id, limit)
            
            if comms:
                context_parts.append("\nRECENT INTERACTIONS:")
                for c in reversed(comms):  # Chronological order for the LLM
                     # Skip empty transcripts
                    if not c.summary and not c.transcript:
                        continue

                    date_str = c.started_at.strftime("%Y-%m-%d") if c.started_at else "Unknown Date"
                    channel = c.channel or c.type
                    
                    # Prefer summary, fall back to truncated transcript
                    content = c.summary
                    if not content and c.transcript:
                        # Truncate transcript to save tokens
                        content = (c.transcript[:500] + '...') if len(c.transcript) > 500 else c.transcript
                    
                    if content:
                        context_parts.append(f"- [{date_str}] ({channel}): {content}")
            
            # 3. Active Context (Existing appointments/deals?)
            # Appointments
            appointments = self.db.query(Appointment).filter(
                Appointment.customer_id == customer_id,
                Appointment.status.in_(["scheduled", "confirmed"])
            ).order_by(Appointment.appointment_date).limit(3).all()
            
            if appointments:
                context_parts.append("\nUPCOMING APPOINTMENTS:")
                for appt in appointments:
                    dt = appt.appointment_date.strftime("%Y-%m-%d %H:%M")
                    context_parts.append(f"- {dt}: {appt.title}")
                    
            # 4. Deals (Active pipeline)
            deals = self.db.query(Deal).filter(
                Deal.customer_id == customer_id,
                Deal.stage.notin_(["closed_won", "closed_lost"])
            ).order_by(desc(Deal.created_at)).limit(3).all()
            
            if deals:
                context_parts.append("\nACTIVE DEALS:")
                for deal in deals:
                    val_str = f"${deal.value/100:.2f}" if deal.value else "Value unknown"
                    stage_str = deal.stage.replace('_', ' ').title()
                    context_parts.append(f"- {deal.title} | Stage: {stage_str} | Value: {val_str}")
                    
            # 5. Campaigns (Active enrollments)
            enrollments = self.db.query(CampaignEnrollment).join(Campaign).filter(
                CampaignEnrollment.customer_id == customer_id,
                CampaignEnrollment.status == "active"
            ).order_by(desc(CampaignEnrollment.created_at)).limit(3).all()
            
            if enrollments:
                context_parts.append("\nACTIVE CAMPAIGNS:")
                for enr in enrollments:
                    context_parts.append(f"- Enrolled in: {enr.campaign.name} (Currently at Step {enr.current_step_order})")
            
            # 6. Analytics (LTV & Engagement)
            total_interactions = self.db.query(func.count(Communication.id)).filter(
                Communication.customer_id == customer_id
            ).scalar() or 0
            
            won_deals_value = self.db.query(func.sum(Deal.value)).filter(
                Deal.customer_id == customer_id,
                Deal.stage == "closed_won"
            ).scalar() or 0
            
            if total_interactions > 0 or won_deals_value > 0:
                context_parts.append("\nCUSTOMER ANALYTICS:")
                context_parts.append(f"- Total Lifetime Value: ${won_deals_value/100:.2f}")
                context_parts.append(f"- Total Lifetime Interactions: {total_interactions}")
                
                # Get sentiment from last 5 comms if available
                recent_sentiments = [c.sentiment for c in self.get_recent_communications(customer_id, 5) if c.sentiment]
                if recent_sentiments:
                    context_parts.append(f"- Recent Sentiment Trend: {', '.join(recent_sentiments)}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"Error building customer context: {e}")
            return ""

    def save_interaction_summary(self, communication_id: str, summary: str):
        """
        Save a summary generated by the LLM back to the communication record
        so it can be retrieved efficiently later.
        """
        comm = self.db.query(Communication).filter(Communication.id == communication_id).first()
        if comm:
            comm.summary = summary
            self.db.commit()
