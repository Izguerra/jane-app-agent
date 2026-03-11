"""
HR & Onboarding Worker (Enterprise)

Target: HR Departments.
Function: Manages candidate screening and onboarding emails.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# Reuse MailboxTools for sending emails
from backend.tools.mailbox_tools import MailboxTools

logger = logging.getLogger("hr-onboarding-worker")

class HROnboardingWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade HR Agent.
    """
    RISK_LEVEL = "medium" # Handles PII
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        candidate_name = input_data.get("candidate_name")
        candidate_email = input_data.get("candidate_email")
        action = input_data.get("action", "onboard") # screen, offer, onboard
        
        if not candidate_name:
            raise ValueError("Missing 'candidate_name'")
            
        task = service.get_task(task_id)
        
        service.update_task_status(task_id, status="running", current_step=f"Initiating {action}...", steps_completed=1, steps_total=3)
        
        # 1. Generate Content (Stub for LLM generation)
        # In prod, this would use the LLM to write a personalized email
        email_subject = ""
        email_body = ""
        
        if action == "offer":
            email_subject = f"Offer of Employment - {candidate_name}"
            email_body = f"Dear {candidate_name},\n\nWe are pleased to offer you the position..."
        elif action == "onboard":
            email_subject = f"Welcome Aboard {candidate_name}!"
            email_body = f"Dear {candidate_name},\n\nWelcome to the team! Here are your next steps..."
        else:
             email_subject = f"Application Update - {candidate_name}"
             email_body = f"Dear {candidate_name},\n\nThank you for your application..."
             
        service.update_task_status(task_id, current_step="Sending Email...", steps_completed=2)
        
        # 2. Send Email via MailboxTools (if email provided)
        email_status = "skipped (no email)"
        if candidate_email:
            try:
                mailbox = MailboxTools(workspace_id=task.workspace_id)
                # Check for active integration first? MailboxTools handles it.
                # But MailboxTools.send_email might raise if not configured.
                
                # Verify we have at least one mailbox
                # For fail-safety, we wrap in try/catch to avoid crashing if no gmail connected
                mailbox.send_email(
                    to_email=candidate_email,
                    subject=email_subject,
                    body=email_body
                )
                email_status = "sent"
                service.add_task_log(task_id, f"Email sent to {candidate_email}")
            except Exception as e:
                service.add_task_log(task_id, f"Email sending failed: {e}", level="warning")
                email_status = f"failed: {str(e)}"
        
        return {
            "candidate": candidate_name,
            "action": action,
            "email_generated": True,
            "email_status": email_status
        }
