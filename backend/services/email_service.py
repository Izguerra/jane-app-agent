import os
import resend
from typing import Optional, List, Dict
import logging

logger = logging.getLogger("email-service")

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API")
        if not self.api_key:
            logger.warning("RESEND_API key not found in environment variables.")
        else:
            resend.api_key = self.api_key

    def send_email(self, to_email: str, subject: str, html_content: str, workspace_id: Optional[str] = None) -> (bool, str):
        """
        Send an email using Resend.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            workspace_id: Optional workspace ID for future multi-tenant config
            
        Returns:
            (bool, str): (True, None) if successful, (False, error_message) otherwise
        """
        if not self.api_key:
            logger.error("Cannot send email: RESEND_API key is missing.")
            return False, "RESEND_API key is missing"

        try:
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
