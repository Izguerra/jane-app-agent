from typing import List, Dict, Any, Optional
import base64
from email.mime.text import MIMEText
from backend.models_db import Integration
from backend.security import decrypt_text
import json
import logging

logger = logging.getLogger("gmail-service")

class GmailService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int) -> Optional[Integration]:
        return self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.provider == "gmail_mailbox",
            Integration.is_active == True
        ).first()

    def _get_service(self, integration: Integration):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        if not integration.credentials:
            raise Exception("No credentials found for Gmail integration")

        creds_data = json.loads(decrypt_text(integration.credentials) if isinstance(integration.credentials, str) else json.dumps(integration.credentials))
        
        creds = Credentials(
            token=creds_data.get("token") or creds_data.get("access_token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes")
        )
        
        return build('gmail', 'v1', credentials=creds)

    def _check_permission(self, integration: Integration, permission: str) -> bool:
        if not integration.settings:
            return False
        settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
        return settings.get(permission, False)

    def list_emails(self, workspace_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Gmail integration not found")
        
        if not self._check_permission(integration, "can_read_emails"):
            raise Exception("Permission denied: Cannot read emails")

        try:
            service = self._get_service(integration)
            results = service.users().messages().list(userId='me', maxResults=limit).execute()
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                # Fetch details for each (batching would be better for perf but keeping simple)
                full_msg = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = full_msg['payload']['headers']
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                emails.append({
                    "id": msg['id'],
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "snippet": full_msg.get('snippet', ''),
                    "provider": "gmail"
                })
                
            return emails
        except Exception as e:
            logger.error(f"Error listing Gmail emails: {e}")
            raise e

    def read_email(self, workspace_id: int, email_id: str) -> Dict[str, Any]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Gmail integration not found")

        if not self._check_permission(integration, "can_read_emails"):
            raise Exception("Permission denied: Cannot read emails")

        try:
            service = self._get_service(integration)
            msg = service.users().messages().get(userId='me', id=email_id).execute()
            
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode()
            elif 'body' in msg['payload']:
                data = msg['payload']['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode()

            return {
                "id": msg['id'],
                "subject": subject,
                "from": sender,
                "to": to,
                "date": date,
                "body": body,
                "snippet": msg.get('snippet', ''),
                "provider": "gmail"
            }
        except Exception as e:
            logger.error(f"Error reading Gmail email: {e}")
            raise e

    def send_email(self, workspace_id: int, to_email: str, subject: str, body: str, cc: List[str] = None, bcc: List[str] = None, is_html: bool = False) -> bool:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Gmail integration not found")

        if not self._check_permission(integration, "can_send_emails"):
            raise Exception("Permission denied: Cannot send emails")

        try:
            service = self._get_service(integration)
            
            message = MIMEText(body, 'html' if is_html else 'plain')
            message['to'] = to_email
            message['subject'] = subject
            
            if cc:
                message['Cc'] = ", ".join(cc)
            
            # BCC headers are not usually set in the message body itself for sending via API, 
            # but for display purposes in some clients they might be. 
            # However, the Gmail API takes the raw message. 
            # IMPORTANT: For Gmail API, recipients are determined by the message headers AND the envelope.
            # But effectively, adding Bcc header to the MIME message is standard for archiving, 
            # though Gmail might strip it for the recipient.
            # The 'raw' message should contain the headers.
            if bcc:
                message['Bcc'] = ", ".join(bcc)

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body_payload = {'raw': raw}
            
            service.users().messages().send(userId='me', body=body_payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error sending Gmail email: {e}")
            raise e

    def search_emails(self, workspace_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id)
        if not integration:
            raise Exception("Gmail integration not found")

        if not self._check_permission(integration, "can_search_emails"):
            raise Exception("Permission denied: Cannot search emails")

        try:
            service = self._get_service(integration)
            results = service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                full_msg = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = full_msg['payload']['headers']
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                emails.append({
                    "id": msg['id'],
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "snippet": full_msg.get('snippet', ''),
                    "provider": "gmail"
                })
                
            return emails
        except Exception as e:
            logger.error(f"Error searching Gmail emails: {e}")
            raise e
