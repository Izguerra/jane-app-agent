from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import logging

from backend.models_db import (
    Campaign, CampaignStep, CampaignEnrollment, 
    Customer, Appointment, Communication
)
from backend.database import generate_comm_id
# Avoid circular imports if possible, or use local imports inside methods

logger = logging.getLogger(__name__)

class CampaignService:
    def __init__(self, db: Session):
        self.db = db

    def create_campaign(self, workspace_id: str, name: str, trigger_type: str, trigger_event: str = None, description: str = None) -> Campaign:
        """Create a new campaign definition."""
        campaign = Campaign(
            id=generate_comm_id(), # Use existing ID generator
            workspace_id=workspace_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_event=trigger_event,
            is_active=True
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def add_step(self, campaign_id: str, step_type: str, config: Dict[str, Any], delay_minutes: int = 0, time_reference: str = 'previous_step', step_order: int = None) -> CampaignStep:
        """Add a step to a campaign."""
        if step_order is None:
            # Auto-calculate order
            last_step = self.db.query(CampaignStep).filter(
                CampaignStep.campaign_id == campaign_id
            ).order_by(desc(CampaignStep.step_order)).first()
            step_order = (last_step.step_order + 1) if last_step else 1

        step = CampaignStep(
            id=generate_comm_id(),
            campaign_id=campaign_id,
            step_order=step_order,
            type=step_type,
            config=config,
            delay_minutes=delay_minutes,
            time_reference=time_reference
        )
        self.db.add(step)
        self.db.commit()
        return step

    def update_step(self, campaign_id: str, step_id: str, step_type: str = None, config: Dict[str, Any] = None, delay_minutes: int = None, time_reference: str = None, step_order: int = None) -> CampaignStep:
        """Update an existing step."""
        step = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id,
            CampaignStep.id == step_id
        ).first()

        if not step:
            return None

        if step_type is not None:
            step.type = step_type
        if config is not None:
            # Merge or replace? Typically replace for full config update. 
            # If partial updates needed, frontend usually sends full object anyway.
            # But let's check input. If config is just a dict, standard practice to replace or deep merge.
            # Here simplistic replace or key update
            if step.config is None:
                 step.config = config
            else:
                 # Update keys
                 # We need to assign a NEW dict to trigger SQLAlchemy change tracking for JSON types mostly
                 new_config = dict(step.config)
                 new_config.update(config)
                 step.config = new_config

        if delay_minutes is not None:
            step.delay_minutes = delay_minutes
        if time_reference is not None:
            step.time_reference = time_reference
        if step_order is not None:
            step.step_order = step_order

        self.db.commit()
        self.db.refresh(step)
        return step

    def delete_step(self, campaign_id: str, step_id: str) -> bool:
        """Delete a step and reorder subsequent steps."""
        step = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id,
            CampaignStep.id == step_id
        ).first()
        
        if not step:
            return False
            
        deleted_order = step.step_order
        self.db.delete(step)
        
        # Reorder subsequent steps
        subsequent_steps = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id,
            CampaignStep.step_order > deleted_order
        ).all()
        
        for s in subsequent_steps:
            s.step_order -= 1
            
        self.db.commit()
        return True

    def trigger_event(self, workspace_id: str, event_name: str, context: Dict[str, Any]):
        """
        Trigger an event (e.g., 'appointment_booked') and enroll eligible customers into matching campaigns.
        """
        logger.info(f"Triggering event {event_name} for workspace {workspace_id} with context {context}")
        
        # 1. Find active campaigns listening for this event
        campaigns = self.db.query(Campaign).filter(
            Campaign.workspace_id == workspace_id,
            Campaign.trigger_type == 'event',
            Campaign.trigger_event == event_name,
            Campaign.is_active == True
        ).all()
        
        if not campaigns:
            logger.info(f"No active campaigns found for event {event_name}")
            return
            
        customer_id = context.get('customer_id')
        reference_id = context.get('reference_id') or context.get('appointment_id')
        
        if not customer_id:
            logger.warning("Cannot enroll: Missing customer_id in context")
            return

        for campaign in campaigns:
            self.enroll_customer(campaign.id, customer_id, reference_id, context)

    def enroll_customer(self, campaign_id: str, customer_id: str, reference_id: str, context: Dict[str, Any]) -> CampaignEnrollment:
        """Enroll a customer into a campaign."""
        # Check for existing active enrollment to avoid duplicates if desired? 
        # For appointments, multiple enrollments are valid if they are different appointments.
        # But same appointment shouldn't double-enroll.
        
        existing = self.db.query(CampaignEnrollment).filter(
            CampaignEnrollment.campaign_id == campaign_id,
            CampaignEnrollment.customer_id == customer_id,
            CampaignEnrollment.reference_id == reference_id,
            CampaignEnrollment.status.in_(['active', 'pending'])
        ).first()
        
        if existing:
            logger.info(f"Customer {customer_id} already enrolled in campaign {campaign_id} for ref {reference_id}")
            return existing

        # Get first step logic
        first_step = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id,
            CampaignStep.step_order == 1
        ).first()
        
        if not first_step:
            logger.warning(f"Campaign {campaign_id} has no steps. Skipping enrollment.")
            return None

        # Calculate run time for first step
        run_at = self._calculate_step_time(first_step, context)
        
        enrollment = CampaignEnrollment(
            id=generate_comm_id(),
            campaign_id=campaign_id,
            customer_id=customer_id,
            reference_id=reference_id,
            current_step_order=1,
            status='active',
            next_run_at=run_at
        )
        self.db.add(enrollment)
        self.db.commit()
        logger.info(f"Enrolled customer {customer_id} in campaign {campaign_id}. first step at {run_at}")
        return enrollment

    def _calculate_step_time(self, step: CampaignStep, context: Dict[str, Any]) -> datetime:
        """Calculate when a step should run based on its config."""
        now = datetime.now(timezone.utc)
        
        # Base time
        if step.time_reference == 'appointment_date':
            appt_date = context.get('appointment_date')
            if isinstance(appt_date, str):
                # Attempt parse if string
                try:
                    appt_date = datetime.fromisoformat(appt_date.replace('Z', '+00:00'))
                except:
                    appt_date = now # Fallback
            
            base_time = appt_date if appt_date else now
            
        elif step.time_reference == 'trigger_time':
            base_time = now
        else:
            # Default to now/previous step completion time (which is effectively 'now' for the first step)
            base_time = now
            
        # Add delay
        # If delay is negative (e.g. -24 hours for "Before Appointment"), timedelta handles it.
        # But usually we store "24 hours before" as -1440 minutes? Or positive + 'before' flag?
        # Let's assume delay_minutes is signed. 
        # Ideally, we should maybe have 'offset_direction' in model, but for now let's assume delay_minutes can be negative if manual entry, 
        # or we update logic.
        # Actually, if we want "24 hours before", we might store delay_minutes = -1440.
        
        run_time = base_time + timedelta(minutes=step.delay_minutes)
        return run_time

    def process_enrollments(self):
        """
        Main worker loop function. 
        Finds enrollments due for execution and runs the current step.
        """
        now = datetime.now(timezone.utc)
        
        due_enrollments = self.db.query(CampaignEnrollment).filter(
            CampaignEnrollment.status == 'active',
            CampaignEnrollment.next_run_at <= now
        ).all()
        
        for enrollment in due_enrollments:
            self._execute_step_for_enrollment(enrollment)

    def _execute_step_for_enrollment(self, enrollment: CampaignEnrollment):
        try:
            # Get current step
            step = self.db.query(CampaignStep).filter(
                CampaignStep.campaign_id == enrollment.campaign_id,
                CampaignStep.step_order == enrollment.current_step_order
            ).first()
            
            if not step:
                # No more steps? Complete.
                enrollment.status = 'completed'
                enrollment.completed_at = datetime.now(timezone.utc)
                enrollment.next_run_at = None
                self.db.commit()
                return

            logger.info(f"Executing step {step.id} ({step.type}) for enrollment {enrollment.id}")
            
            # EXECUTE ACTION
            success, err_msg = self._run_step_action(step, enrollment)
            
            if success:
                # Move to next step
                next_step = self.db.query(CampaignStep).filter(
                    CampaignStep.campaign_id == enrollment.campaign_id,
                    CampaignStep.step_order == step.step_order + 1
                ).first()
                
                if next_step:
                    enrollment.current_step_order = next_step.step_order
                    # Calculate next time
                    # Need context for Time Reference! 
                    # We need to reconstruct context. e.g. appointment date.
                    context = self._rehydrate_context(enrollment)
                    enrollment.next_run_at = self._calculate_step_time(next_step, context)
                    
                    # If time_reference was 'previous_step', base it on NOW
                    if next_step.time_reference == 'previous_step':
                         enrollment.next_run_at = datetime.now(timezone.utc) + timedelta(minutes=next_step.delay_minutes)
                         
                else:
                    enrollment.status = 'completed'
                    enrollment.completed_at = datetime.now(timezone.utc)
                    enrollment.next_run_at = None
            else:
                # Retry logic or fail?
                # For now, mark failed
                enrollment.status = 'failed'
                enrollment.error_message = err_msg or "Step execution failed"
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing enrollment {enrollment.id}: {e}")
            enrollment.status = 'error'
            enrollment.error_message = str(e)
            self.db.commit()

    def _run_step_action(self, step: CampaignStep, enrollment: CampaignEnrollment) -> (bool, str):
        """Perform the actual SMS/Email/Call. Returns (success, error_message)."""
        # Get customer
        customer = self.db.query(Customer).filter(Customer.id == enrollment.customer_id).first()
        if not customer:
            logger.error(f"Customer {enrollment.customer_id} not found for enrollment {enrollment.id}")
            return False, "Customer not found"
            
        # Get Context Data (e.g. appointment date)
        context = self._rehydrate_context(enrollment)
            
        try:
            if step.type == 'sms':
                if not customer.phone:
                    logger.warning(f"Customer {customer.id} has no phone. Skipping SMS step.")
                    return True, "Skipped (No phone)"
                
                # Render template
                template = step.config.get('template_body', '')
                message_body = self._render_template(template, customer, context)
                
                # Send SMS
                from backend.services.sms_service import send_sms
                logger.info(f"Sending SMS to {customer.phone}: {message_body}")
                
                success, sms_err = send_sms(customer.phone, message_body, workspace_id=step.campaign.workspace_id)
                if not success:
                    raise Exception(f"SMS send failed: {sms_err}")

            elif step.type == 'email':
                if not customer.email:
                    logger.warning(f"Customer {customer.id} has no email. Skipping Email step.")
                    return True, "Skipped (No email)"
                
                subject_template = step.config.get('subject', 'Update')
                subject = self._render_template(subject_template, customer, context)
                
                template = step.config.get('template_body', '')
                body = self._render_template(template, customer, context)
                
                
                logger.info(f"Sending Email to {customer.email}: Subject: {subject}")
                
                from backend.services.email_service import EmailService
                email_service = EmailService()
                success, email_err = email_service.send_email(customer.email, subject, body, step.campaign.workspace_id)
                
                if not success:
                    raise Exception(f"Email send failed: {email_err}")
                
            elif step.type == 'whatsapp':
                if not customer.phone:
                    logger.warning(f"Customer {customer.id} has no phone. Skipping WhatsApp step.")
                    return True, "Skipped (No phone)"

                template = step.config.get('template_body', '')
                message_body = self._render_template(template, customer, context)
                
                logger.info(f"Sending WhatsApp message to {customer.phone} via Twilio")
                
                from backend.services.sms_service import send_sms
                # Using force_whatsapp=True to treat as WhatsApp channel
                success, wa_err = send_sms(customer.phone, message_body, workspace_id=step.campaign.workspace_id, force_whatsapp=True)
                
                if not success:
                    raise Exception(f"WhatsApp send failed: {wa_err}")
                
            elif step.type == 'wait':
                # Wait step simply completes. The logic for 'next_run_at' of the NEXT step will obey the delay of that step?
                # OR does the Wait step imply the delay happens NOW?
                # Usually: Step 1 (SMS) -> Step 2 (Wait 24h) -> Step 3 (SMS).
                # Implementation: 
                # Step 1 runs.
                # Next step is Step 2 (Wait).
                # enrollment.next_run_at calculated for Step 2 based on Step 2's delay/time_ref.
                # ... Time passes ...
                # Worker picks up Step 2.
                # Runs _run_step_action for Step 2 (Wait). Returns True immediately.
                # Move to Step 3.
                # enrollment.next_run_at calculated for Step 3 based on Step 3's delay/time_ref.
                # IF Step 3 has 0 delay, it runs immediately? 
                # So a "Wait" step needs to actually enforce a delay for the *next* step if the next step doesn't have one?
                # OR usually, the "Wait" step has a delay_minutes of 24h. 
                # So it waits 24h BEFORE it runs. Once it runs, it finishes instantly.
                # Check logic: enrollment.next_run_at is when the step *starts*.
                # So if Step 2 is "Wait 24h", we set next_run_at = now + 24h.
                # Worker wakes up in 24h. Runs Step 2.
                # Step 2 finishes.
                # Moves to Step 3. 
                # If Step 3 has 0 delay, it runs immediately.
                # YES, this logic works. The "Wait" happens *before* the step executes.
                pass

            elif step.type == 'call':
                 logger.info(f"Simulating AI Call to {customer.phone}")

            else:
                logger.warning(f"Unknown step type: {step.type}")
                return False, f"Unknown step type: {step.type}"

        except Exception as e:
            logger.error(f"Error executing step action: {e}")
            return False, str(e)

        return True, None
    def _render_template(self, template: str, customer: Customer, context: Dict[str, Any] = None) -> str:
        """Simple template replacement with context support."""
        text = template
        # Basic replacement
        first = customer.first_name or "there"
        last = customer.last_name or ""
        text = text.replace("{{first_name}}", first)
        text = text.replace("{{last_name}}", last)
        
        # Context replacement
        if context:
            for key, value in context.items():
                if value is not None:
                     val_str = str(value)
                     try:
                         # Timezone conversion to Eastern Time (hardcoded default)
                         from datetime import datetime, timezone
                         try:
                             from zoneinfo import ZoneInfo
                             target_tz = ZoneInfo("America/New_York")
                         except ImportError:
                             import pytz
                             target_tz = pytz.timezone("America/New_York")

                         dt = None
                         if hasattr(value, 'astimezone'): # datetime object
                             dt = value
                         elif isinstance(value, str):
                             try:
                                 dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                             except ValueError:
                                 pass
                         
                         if dt:
                             if dt.tzinfo is None:
                                 dt = dt.replace(tzinfo=timezone.utc)
                             dt_local = dt.astimezone(target_tz)
                             # Format: Jan 12, 10:00 PM
                             val_str = dt_local.strftime("%b %d, %I:%M %p")
                     except Exception as e:
                         pass

                     text = text.replace(f"{{{{{key}}}}}", val_str)
        
        return text

    def handle_inbound_message(self, workspace_id: str, customer_id: str):
        """
        Handle an inbound message event.
        If the customer has an active campaign with 'stop_on_response' enabled, cancel it.
        """
        logger.info(f"Handling inbound message from customer {customer_id} in workspace {workspace_id}")
        
        # Find active enrollments for this customer where campaign has stop_on_response=True
        active_enrollments = self.db.query(CampaignEnrollment).join(Campaign).filter(
            CampaignEnrollment.customer_id == customer_id,
            CampaignEnrollment.status.in_(['active', 'pending']),
            Campaign.stop_on_response == True,
            Campaign.workspace_id == workspace_id
        ).all()
        
        if active_enrollments:
            for enrollment in active_enrollments:
                logger.info(f"Stopping campaign enrollment {enrollment.id} (Campaign {enrollment.campaign_id}) due to user response.")
                enrollment.status = 'cancelled'
                enrollment.error_message = "Stopped by user response"
                enrollment.completed_at = datetime.now(timezone.utc)
            
            self.db.commit()

    def _rehydrate_context(self, enrollment: CampaignEnrollment) -> Dict[str, Any]:
        """Re-fetch appointment or other data needed for timing."""
        context = {}
        if enrollment.reference_id:
             # Try finding appointment
             appt = self.db.query(Appointment).filter(Appointment.id == enrollment.reference_id).first()
             if appt:
                 context['appointment_date'] = appt.appointment_date
                 context['appointment_id'] = appt.id
        return context
