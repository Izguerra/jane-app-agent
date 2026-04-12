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

    @llm.function_tool(description="List the most recent emails from the user's inbox (Gmail, Outlook, or iCloud). This shows subjects, senders, and dates.")
    async def list_inbox_emails(self, limit: int = 10):
        """
        Fetch a summary of recent emails.
        
        Args:
            limit: How many emails to fetch (default 10).
        """
        from backend.database import SessionLocal
        from backend.services.gmail_service import GmailService
        from backend.services.outlook_service import OutlookService
        from backend.services.icloud_service import ICloudService
        
        db = SessionLocal()
        try:
            results = []
            # Check for Gmail
            try:
                gmail = GmailService(db)
                gmail_emails = gmail.list_emails(self.workspace_id, limit=limit)
                results.extend(gmail_emails)
            except Exception: pass # Skip if not configured or permission denied
            
            # Check for Outlook
            try:
                outlook = OutlookService(db)
                outlook_emails = outlook.list_emails(self.workspace_id, limit=limit)
                results.extend(outlook_emails)
            except Exception: pass
            
            # Check for iCloud
            try:
                icloud = ICloudService(db)
                icloud_emails = icloud.list_emails(self.workspace_id, limit=limit)
                results.extend(icloud_emails)
            except Exception: pass
            
            if not results:
                return "No active email integrations found or permission to read emails is disabled in Integrations settings."
                
            # Sort by date (naive string sort usually works for these ISO strings, but it's just a summary)
            # results.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            summary = "Recent Emails:\n"
            for i, em in enumerate(results[:limit]):
                summary += f"{i+1}. [{em.get('provider').upper()}] From: {em.get('from')} | Subject: {em.get('subject')} | Date: {em.get('date')}\n"
                summary += f"   ID: {em.get('id')} (use this ID to read full body)\n"
            
            return summary
        except Exception as e:
            return f"Error listing emails: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(description="Read the full content of a specific email. You must provide the email_id and provider type from the list_inbox_emails tool.")
    async def read_email_details(self, email_id: str, provider: str):
        """
        Fetch the full body of an email.
        
        Args:
            email_id: The unique identifier for the email.
            provider: The provider type (e.g. 'gmail', 'outlook', 'icloud').
        """
        from backend.database import SessionLocal
        from backend.services.gmail_service import GmailService
        from backend.services.outlook_service import OutlookService
        from backend.services.icloud_service import ICloudService
        
        db = SessionLocal()
        try:
            provider = provider.lower()
            if provider == "gmail":
                service = GmailService(db)
            elif provider == "outlook":
                service = OutlookService(db)
            elif provider == "icloud":
                service = ICloudService(db)
            else:
                return f"Error: Unsupported provider '{provider}'."
                
            detail = service.read_email(self.workspace_id, email_id)
            return f"Email Details:\nFrom: {detail.get('from')}\nTo: {detail.get('to')}\nSubject: {detail.get('subject')}\nDate: {detail.get('date')}\n\nBody:\n{detail.get('body')}"
        except Exception as e:
            return f"Error reading email: {str(e)}"
        finally:
            db.close()
