import asyncio
from livekit.agents import llm

class CommunicationMixin:
    @llm.function_tool(description="Send an SMS text message to a customer.")
    async def send_sms_notification(self, phone_number: str, message: str):
        if not phone_number or not message: return "Error: Missing info."
        try:
            from backend.services.sms_service import send_sms
            # Use asyncio.to_thread to prevent blocking the event loop with synchronous Twilio/Telnyx calls
            success, error = await asyncio.to_thread(send_sms, phone_number, message, self.workspace_id)
            return "SMS sent." if success else f"Failed: {error}"
        except Exception as e: return f"Error: {str(e)}"

    @llm.function_tool(description="Send an email notification to a customer.")
    async def send_email_notification(self, email_address: str, subject: str, message: str):
        if not email_address or not subject or not message: return "Error: Missing info."
        try:
            from backend.services.email_service import EmailService
            service = EmailService()
            # Use asyncio.to_thread to prevent blocking the event loop with synchronous Resend calls
            success, error = await asyncio.to_thread(
                service.send_email, 
                to_email=email_address, 
                subject=subject, 
                html_content=f"<p>{message}</p>", 
                workspace_id=self.workspace_id
            )
            return "Email sent." if success else f"Failed: {error}"
        except Exception as e: return f"Error: {str(e)}"
