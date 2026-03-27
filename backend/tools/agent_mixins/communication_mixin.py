import re
import asyncio
from livekit.agents import llm

def _normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format. Auto-adds +1 for 10-digit North American numbers."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    if len(digits) > 10:
        return f"+{digits}"
    return f"+{digits}"

class CommunicationMixin:
    @llm.function_tool(description="Send an SMS text message to a customer. IMPORTANT: Always include the country code (e.g. +1 for US/Canada). If the user provides a 10-digit number, automatically prepend +1.")
    async def send_sms_notification(self, phone_number: str, message: str):
        if not phone_number or not message: return "Error: Missing info."
        try:
            from backend.services.sms_service import send_sms
            normalized = _normalize_phone(phone_number)
            # Run blocking database and network operations in a thread pool to avoid hanging the asyncio event loop
            success, error = await asyncio.to_thread(send_sms, normalized, message, self.workspace_id)
            return f"SMS sent to {normalized}." if success else f"Failed: {error}"
        except Exception as e: return f"Error: {str(e)}"

    @llm.function_tool(description="Send an email notification to a customer.")
    async def send_email_notification(self, email_address: str, subject: str, message: str):
        if not email_address or not subject or not message: return "Error: Missing info."
        try:
            from backend.services.email_service import EmailService
            service = EmailService()
            # Run blocking network operations (Resend API) in a thread pool
            success, error = await asyncio.to_thread(
                service.send_email,
                to_email=email_address, 
                subject=subject, 
                html_content=f"<p>{message}</p>", 
                workspace_id=self.workspace_id
            )
            return "Email sent." if success else f"Failed: {error}"
        except Exception as e: return f"Error: {str(e)}"
