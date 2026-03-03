from typing import List, Dict, Any, Optional
import requests
import json
import logging
from datetime import datetime
from backend.models_db import Integration
from backend.security import decrypt_text

logger = logging.getLogger("outlook-service")

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

class OutlookService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int, provider: str) -> Optional[Integration]:
        # provider can be 'outlook_mailbox' or 'outlook_calendar'
        return self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.provider == provider,
            Integration.is_active == True
        ).first()

    def _get_headers(self, integration: Integration) -> Dict[str, str]:
        if not integration.credentials:
            raise Exception("No credentials found for Outlook integration")

        creds_data = json.loads(decrypt_text(integration.credentials) if isinstance(integration.credentials, str) else json.dumps(integration.credentials))
        
        # Access Token should be refreshed if expired (TODO: Implement refresh logic)
        access_token = creds_data.get("access_token")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _check_permission(self, integration: Integration, permission: str) -> bool:
        if not integration.settings:
            return False
        settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
        return settings.get(permission, False)

    # --- EMAIL METHODS ---

    def list_emails(self, workspace_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "outlook_mailbox")
        if not integration:
            raise Exception("Outlook Mail integration not found")
        
        if not self._check_permission(integration, "can_read_emails"):
            raise Exception("Permission denied: Cannot read emails")

        try:
            headers = self._get_headers(integration)
            response = requests.get(
                f"{GRAPH_API_URL}/me/messages?$top={limit}&$select=id,subject,from,receivedDateTime,bodyPreview",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            emails = []
            for msg in data.get('value', []):
                emails.append({
                    "id": msg['id'],
                    "subject": msg.get('subject', '(No Subject)'),
                    "from": msg.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
                    "date": msg.get('receivedDateTime', ''),
                    "snippet": msg.get('bodyPreview', ''),
                    "provider": "outlook"
                })
                
            return emails
        except Exception as e:
            logger.error(f"Error listing Outlook emails: {e}")
            raise e

    def read_email(self, workspace_id: int, email_id: str) -> Dict[str, Any]:
        integration = self._get_integration(workspace_id, "outlook_mailbox")
        if not integration:
            raise Exception("Outlook Mail integration not found")

        try:
            headers = self._get_headers(integration)
            response = requests.get(
                f"{GRAPH_API_URL}/me/messages/{email_id}",
                headers=headers
            )
            response.raise_for_status()
            msg = response.json()
            
            return {
                "id": msg['id'],
                "subject": msg.get('subject', '(No Subject)'),
                "from": msg.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
                "to": "; ".join([r['emailAddress']['address'] for r in msg.get('toRecipients', [])]),
                "date": msg.get('receivedDateTime', ''),
                "body": msg.get('body', {}).get('content', ''),
                "snippet": msg.get('bodyPreview', ''),
                "provider": "outlook"
            }
        except Exception as e:
            logger.error(f"Error reading Outlook email: {e}")
            raise e

    def send_email(self, workspace_id: int, to_email: str, subject: str, body: str) -> bool:
        integration = self._get_integration(workspace_id, "outlook_mailbox")
        if not integration:
            raise Exception("Outlook Mail integration not found")

        if not self._check_permission(integration, "can_send_emails"):
            raise Exception("Permission denied: Cannot send emails")

        try:
            headers = self._get_headers(integration)
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{GRAPH_API_URL}/me/sendMail",
                headers=headers,
                json=email_data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending Outlook email: {e}")
            raise e
    
    def search_emails(self, workspace_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "outlook_mailbox")
        if not integration:
            raise Exception("Outlook Mail integration not found")
        
        try:
            headers = self._get_headers(integration)
            # Graph API uses $search parameter
            response = requests.get(
                f"{GRAPH_API_URL}/me/messages?$search=\"{query}\"&$top={limit}&$select=id,subject,from,receivedDateTime,bodyPreview",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            emails = []
            for msg in data.get('value', []):
                emails.append({
                    "id": msg['id'],
                    "subject": msg.get('subject', '(No Subject)'),
                    "from": msg.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
                    "date": msg.get('receivedDateTime', ''),
                    "snippet": msg.get('bodyPreview', ''),
                    "provider": "outlook"
                })
            return emails
        except Exception as e:
            logger.error(f"Error searching Outlook emails: {e}")
            raise e

    # --- CALENDAR METHODS ---
    
    def list_events(self, workspace_id: int, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "outlook_calendar")
        if not integration:
            # Try finding generic exchange/outlook integration if specific calendar one missing?
            # For now strictly separate as per design
            return []
            
        if not self._check_permission(integration, "can_view_events"):
            return []
            
        try:
            headers = self._get_headers(integration)
            start_str = start_dt.isoformat()
            end_str = end_dt.isoformat()
            
            response = requests.get(
                f"{GRAPH_API_URL}/me/calendarView?startDateTime={start_str}&endDateTime={end_str}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            events = []
            for evt in data.get('value', []):
                events.append({
                    "id": evt['id'],
                    "title": evt.get('subject', 'No Title'),
                    "start": evt.get('start', {}).get('dateTime'),
                    "end": evt.get('end', {}).get('dateTime'),
                    "description": evt.get('bodyPreview', ''),
                    "provider": "outlook_calendar"
                })
            return events
        except Exception as e:
            logger.error(f"Error listing Outlook events: {e}")
            return []
            
    def create_event(self, workspace_id: int, title: str, start_dt: datetime, end_dt: datetime, description: str = "") -> Dict[str, Any]:
        integration = self._get_integration(workspace_id, "outlook_calendar")
        if not integration:
            raise Exception("Outlook Calendar integration not found")
            
        if not self._check_permission(integration, "can_create_events"):
            raise Exception("Permission denied: Cannot create events")
            
        try:
            headers = self._get_headers(integration)
            event_data = {
                "subject": title,
                "body": {
                    "contentType": "HTML",
                    "content": description
                },
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "UTC"
                }
            }
            
            response = requests.post(
                f"{GRAPH_API_URL}/me/events",
                headers=headers,
                json=event_data
            )
            response.raise_for_status()
            evt = response.json()
            
            return {
                "id": evt['id'],
                "title": evt.get('subject'),
                "start": evt.get('start', {}).get('dateTime'),
                "end": evt.get('end', {}).get('dateTime'),
                "provider": "outlook_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            logger.error(f"Error creating Outlook event: {e}")
            raise e

    def get_event(self, workspace_id: int, event_id: str) -> Optional[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "outlook_calendar")
        if not integration:
            return None
            
        try:
            headers = self._get_headers(integration)
            response = requests.get(
                f"{GRAPH_API_URL}/me/events/{event_id}",
                headers=headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            evt = response.json()
            
            return {
                "id": evt['id'],
                "title": evt.get('subject', 'No Title'),
                "start": evt.get('start', {}).get('dateTime'),
                "end": evt.get('end', {}).get('dateTime'),
                "description": evt.get('bodyPreview', ''),
                "provider": "outlook_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            logger.error(f"Error getting Outlook event: {e}")
            return None

    def update_event(self, workspace_id: int, event_id: str, start_time: datetime = None, end_time: datetime = None, title: str = None, description: str = None) -> Dict[str, Any]:
        integration = self._get_integration(workspace_id, "outlook_calendar")
        if not integration:
            raise Exception("Outlook Calendar integration not found")
            
        if not self._check_permission(integration, "can_edit_events"):
             # Fallback if specific permission missing? 
             pass

        try:
            headers = self._get_headers(integration)
            
            update_data = {}
            if title:
                update_data['subject'] = title
            if description:
                update_data['body'] = {
                    "contentType": "HTML",
                    "content": description
                }
            
            if start_time and end_time:
                 update_data['start'] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC"
                }
                 update_data['end'] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC"
                }
            
            response = requests.patch(
                f"{GRAPH_API_URL}/me/events/{event_id}",
                headers=headers,
                json=update_data
            )
            response.raise_for_status()
            evt = response.json()
            
            return {
                "id": evt['id'],
                "title": evt.get('subject'),
                "start": evt.get('start', {}).get('dateTime'),
                "end": evt.get('end', {}).get('dateTime'),
                "provider": "outlook_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            logger.error(f"Error updating Outlook event: {e}")
            raise e

    def delete_event(self, workspace_id: int, event_id: str) -> bool:
        integration = self._get_integration(workspace_id, "outlook_calendar")
        if not integration:
            return False
            
        try:
            headers = self._get_headers(integration)
            response = requests.delete(
                f"{GRAPH_API_URL}/me/events/{event_id}",
                headers=headers
            )
            if response.status_code == 204:
                return True
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting Outlook event: {e}")
            return False
