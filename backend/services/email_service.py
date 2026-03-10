import os
import resend
from typing import Optional, List, Dict
import logging

logger = logging.getLogger("email-service")

from backend.services.integration_service import IntegrationService

class EmailService:
    def __init__(self):
        # We fetch keys dynamically during send_email to support multi-tenancy
        pass

    def send_email(self, to_email: str, subject: str, html_content: str, workspace_id: Optional[str] = None) -> (bool, str):
        """
        Send an email using Resend.
        """
        api_key = IntegrationService.get_provider_key(
            workspace_id=workspace_id,
            provider="resend",
            env_fallback="RESEND_API"
        )

        if not api_key:
            logger.error(f"Cannot send email: API key is missing for workspace {workspace_id}.")
            return False, "Email API key is missing"

        try:
            resend.api_key = api_key
            # TODO: Configure 'from' address based on workspace or default
            from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev") 
            
            logger.info(f"Sending email to {to_email} via Resend")
            
            params = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }

            email = resend.Emails.send(params)
            logger.info(f"Email sent successfully. ID: {email.get('id')}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False, str(e)
