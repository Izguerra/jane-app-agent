from typing import Optional, List, Dict, Any
from backend.services.gmail_service import GmailService
from backend.services.outlook_service import OutlookService
from backend.services.icloud_service import ICloudService
from backend.database import SessionLocal
import json

class MailboxTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    def get_connected_providers(self) -> List[str]:
        """
        Get list of active mailbox providers for this workspace.
        Returns list like ['gmail_mailbox', 'outlook_mailbox']
        """
        from backend.models_db import Integration
        db = SessionLocal()
        try:
            integrations = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider.in_(['gmail_mailbox', 'outlook_mailbox', 'icloud_mailbox']),
                Integration.is_active == True
            ).all()
            return [i.provider for i in integrations]
        finally:
            db.close()

    def list_emails(self, provider: str = None, limit: int = 10) -> str:
        """
        List recent emails from connected mailboxes.
        If only one provider is connected, uses it automatically.
        :param provider: specific provider to check ('gmail', 'outlook', 'icloud'). If None, auto-detects.
        :param limit: max emails to return per provider
        :return: JSON string of emails
        """
        db = SessionLocal()
        all_emails = []
        errors = []
        
        # Auto-detect provider if not specified
        if not provider:
            connected = self.get_connected_providers()
            if len(connected) == 1:
                provider = connected[0]
                print(f"DEBUG: Auto-detected single provider: {provider}")
            elif len(connected) > 1:
                # Multiple providers - check all
                print(f"DEBUG: Multiple providers connected: {connected}")
            else:
                return "No mailbox integrations are connected. Please connect Gmail, Outlook, or iCloud in Integrations."
        
        # Normalize provider name
        if provider:
            if 'gmail' in provider.lower():
                provider = 'gmail_mailbox'
            elif 'outlook' in provider.lower():
                provider = 'outlook_mailbox'
            elif 'icloud' in provider.lower():
                provider = 'icloud_mailbox'
        
        try:
            # Gmail
            if not provider or provider == 'gmail_mailbox':
                try:
                    service = GmailService(db)
                    emails = service.list_emails(self.workspace_id, limit)
                    all_emails.extend(emails)
                except Exception as e:
                    if "integration not found" not in str(e).lower():
                        print(f"Gmail list error: {e}")
                        errors.append(f"Gmail: {str(e)}")

            # Outlook
            if not provider or provider == 'outlook_mailbox':
                try:
                    service = OutlookService(db)
                    emails = service.list_emails(self.workspace_id, limit)
                    all_emails.extend(emails)
                except Exception as e:
                    if "integration not found" not in str(e).lower():
                        print(f"Outlook list error: {e}")
                        errors.append(f"Outlook: {str(e)}")

            # iCloud
            if not provider or provider == 'icloud_mailbox':
                try:
                    service = ICloudService(db)
                    emails = service.list_emails(self.workspace_id, limit)
                    all_emails.extend(emails)
                except Exception as e:
                    if "integration not found" not in str(e).lower():
                        print(f"iCloud list error: {e}")
                        errors.append(f"iCloud: {str(e)}")

            if not all_emails:
                if errors:
                    return f"Failed to retrieve emails. Errors: {'; '.join(errors)}"
                return "No emails found or no mailbox integrations active."

            # Sort by date desc (simple string sort might fail if formats differ, but services usually return ISO or recent first)
            return json.dumps(all_emails, indent=2)
        finally:
            db.close()

    def read_email(self, email_id: str, provider: str) -> str:
        """
        Read content of a specific email.
        :param email_id: ID of the email
        :param provider: Provider of the email ('gmail', 'outlook', 'icloud') - usually returned by list_emails
        :return: JSON string of email details
        """
        db = SessionLocal()
        try:
            provider = provider.lower()
            if 'gmail' in provider:
                service = GmailService(db)
                email = service.read_email(self.workspace_id, email_id)
            elif 'outlook' in provider:
                service = OutlookService(db)
                email = service.read_email(self.workspace_id, email_id)
            elif 'icloud' in provider:
                service = ICloudService(db)
                email = service.read_email(self.workspace_id, email_id)
            else:
                return f"Unknown provider: {provider}"

            return json.dumps(email, indent=2)
        except Exception as e:
            return f"Error reading email: {str(e)}"
        finally:
            db.close()

    def send_email(self, to_email: str, subject: str, body: str, provider: str = None, cc: List[str] = None, bcc: List[str] = None, is_html: bool = False) -> str:
        """
        Send an email.
        :param to_email: Recipient
        :param subject: Subject line
        :param body: Email body (text/html)
        :param provider: specific provider to use. If None, uses first available active integration.
        :param cc: List of CC recipients
        :param bcc: List of BCC recipients
        :param is_html: Whether the body is HTML
        :return: Confirmation message
        """
        from backend.models_db import WorkerTask
        from datetime import datetime, timedelta
        import uuid
        
        db = SessionLocal()
        try:
            # --- GUARD RAIL 1: Duplicate Check (5 minutes) ---
            five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
            # Find recent tasks for email-worker that match recipient/subject
            recent_dupes = db.query(WorkerTask).filter(
                WorkerTask.workspace_id == self.workspace_id,
                WorkerTask.worker_type == "email-worker",
                WorkerTask.created_at >= five_mins_ago,
                WorkerTask.status == "completed"
            ).all()
            
            for task in recent_dupes:
                # Check output or input for match
                # Since we are checking *Direct* sends too, we need to check the inputs we saved (if any) or output
                # Let's check input_data primarily
                data = task.input_data or {}
                if data.get("recipient") == to_email and data.get("subject") == subject:
                    # Potential dupe
                    return f"SAFETY BLOCK: A similar email to {to_email} with subject '{subject}' was sent less than 5 minutes ago. Please wait before sending again."

            # --- END GUARD RAIL ---

            # 1. Determine provider if not specified
            active_service = None
            service_name = ""

            if provider:
                if 'gmail' in provider:
                    active_service = GmailService(db)
                    service_name = "Gmail"
                elif 'outlook' in provider:
                    active_service = OutlookService(db)
                    service_name = "Outlook"
                elif 'icloud' in provider:
                    active_service = ICloudService(db)
                    service_name = "iCloud"
            else:
                # Try discovery
                # Check Gmail
                try:
                    svc = GmailService(db)
                    if svc._get_integration(self.workspace_id):
                        active_service = svc
                        service_name = "Gmail"
                except: pass

                if not active_service:
                    try:
                        svc = OutlookService(db)
                        if svc._get_integration(self.workspace_id, "outlook_mailbox"):
                            active_service = svc
                            service_name = "Outlook"
                    except: pass
                
                if not active_service:
                    try:
                        svc = ICloudService(db)
                        if svc._get_integration(self.workspace_id, "icloud_mailbox"):
                            active_service = svc
                            service_name = "iCloud"
                    except: pass

            if not active_service:
                logger.warning(f"No active mailbox integration found for workspace {self.workspace_id}")
                return "No active mailbox integration found to send email."

            # --- GUARD RAIL 2: Integration Permissions Check ---
            try:
                from backend.models_db import Integration
                import json
                
                prov_str = ""
                if service_name == "Gmail": prov_str = "gmail_mailbox"
                elif service_name == "Outlook": prov_str = "outlook_mailbox"
                elif service_name == "iCloud": prov_str = "icloud_mailbox"
                
                if prov_str:
                    integ_record = db.query(Integration).filter(
                        Integration.workspace_id == self.workspace_id,
                        Integration.provider == prov_str,
                        Integration.is_active == True
                    ).first()
                    
                    if integ_record and integ_record.settings:
                        start_settings = json.loads(integ_record.settings) if isinstance(integ_record.settings, str) else integ_record.settings
                        # Use consistent 'can_send_emails' key
                        permission_granted = start_settings.get("can_send_emails", True)
                        if not permission_granted:
                            logger.error(f"Permission denied for {service_name} (can_send_emails=False)")
                            return f"PERMISSION DENIED: The '{service_name}' integration has 'Send emails' disabled in settings."
            except Exception as perm_e:
                logger.warning(f"Permission check error: {perm_e}")
            # --- END GUARD RAIL ---

            logger.info(f"Dispatching email to {to_email} via {service_name}")

            if service_name == "Gmail":
                success = active_service.send_email(self.workspace_id, to_email, subject, body, cc=cc, bcc=bcc, is_html=is_html)
            else:
                # Other services might not support CC/BCC/HTML yet, fall back to basic
                success = active_service.send_email(self.workspace_id, to_email, subject, body)
                
            if success:
                # --- AUDIT LOGGING ---
                # Silently create a COMPLETED task record so it shows in dashboard
                try:
                    audit_task = WorkerTask(
                        id=str(uuid.uuid4()),
                        workspace_id=self.workspace_id,
                        worker_type="email-worker",
                        status="completed",
                        input_data={
                            "action": "send",
                            "recipient": to_email,
                            "subject": subject,
                            "body": body,
                            "via": "direct_tool"
                        },
                        output_data={"result": "Sent via Chatbot/Voice"},
                        steps_completed=1,
                        steps_total=1,
                        completed_at=datetime.utcnow()
                    )
                    db.add(audit_task)
                    db.commit()
                except Exception as log_e:
                    print(f"Failed to audit log email: {log_e}")
                # --- END AUDIT ---
                
                return f"Email sent successfully via {service_name}."
            else:
                return "Failed to send email."
        except Exception as e:
            return f"Error sending email: {str(e)}"
        finally:
            db.close()

    def search_emails(self, query: str, limit: int = 10, provider: str = None) -> str:
        """
        Search for emails matching a query.
        If only one provider is connected, uses it automatically.
        :param query: Search term (sender, subject, content)
        :param limit: Max results
        :param provider: Optional specific provider. If None, auto-detects.
        :return: JSON string of results
        """
        db = SessionLocal()
        all_emails = []
        
        # Auto-detect provider if not specified
        if not provider:
            connected = self.get_connected_providers()
            if len(connected) == 1:
                provider = connected[0]
                print(f"DEBUG: search_emails auto-detected single provider: {provider}")
        
        try:
             # Gmail
            if not provider or 'gmail' in provider:
                try:
                    service = GmailService(db)
                    emails = service.search_emails(self.workspace_id, query, limit)
                    all_emails.extend(emails)
                except: pass

            # Outlook
            if not provider or 'outlook' in provider:
                try:
                    service = OutlookService(db)
                    emails = service.search_emails(self.workspace_id, query, limit)
                    all_emails.extend(emails)
                except: pass

            # iCloud
            if not provider or 'icloud' in provider:
                try:
                    service = ICloudService(db)
                    emails = service.search_emails(self.workspace_id, query, limit)
                    all_emails.extend(emails)
                except: pass

            if not all_emails:
                return f"No emails found matching '{query}'."

            return json.dumps(all_emails, indent=2)
        finally:
            db.close()
