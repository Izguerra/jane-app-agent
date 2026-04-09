from livekit.agents import llm

class CommunicationMixin:
    @llm.function_tool(description="Send an SMS text message to a phone number. IMPORTANT: Always include the country code (e.g., +1 for US/Canada). If the user provides a 10-digit number without a country code, assume +1 (North America) and prepend it automatically. Example: '4167865786' should become '+14167865786'.")
    async def send_sms_notification(self, phone_number: str, message: str):
        """
        Send an SMS text message to a phone number.
        
        Args:
            phone_number: The recipient's phone number in E.164 format (e.g., +14167865786).
            message: The message body to send.
        """
        if not phone_number or not message: return "Error: Missing info."
        
        try:
            from backend.services.sms_service import send_sms
            success, error = send_sms(phone_number, message, self.workspace_id)
            return "SMS sent successfully." if success else f"Failed to send SMS: {error}"
        except Exception as e: return f"Error sending SMS: {str(e)}"

    @llm.function_tool(description="Send an email to a recipient. IMPORTANT: Before calling this tool, carefully confirm the email address with the user by spelling it back. Email addresses must be in the format 'user@domain.com'.")
    async def send_email_notification(self, email_address: str, subject: str, message: str):
        """
        Send an email to a recipient.
        
        Args:
            email_address: The recipient's email address (e.g., randy@supaagent.com).
            subject: The subject line of the email.
            message: The body of the email (plain text).
        """
        if not email_address or not subject or not message: return "Error: Missing info."
        
        try:
            from backend.services.email_service import EmailService
            service = EmailService()
            success, error = service.send_email(to_email=email_address, subject=subject, html_content=f"<p>{message}</p>", workspace_id=self.workspace_id)
            return "Email sent successfully." if success else f"Failed to send email: {error}"
        except Exception as e: return f"Error sending email: {str(e)}"
