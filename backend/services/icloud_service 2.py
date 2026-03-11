from typing import List, Dict, Any, Optional
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
import logging
import json
from backend.models_db import Integration
from backend.security import decrypt_text

import caldav
from caldav.elements import dav, cdav
from datetime import datetime

logger = logging.getLogger("icloud-service")

class ICloudService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int, provider: str) -> Optional[Integration]:
        return self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.provider == provider,
            Integration.is_active == True
        ).first()

    def _get_credentials(self, integration: Integration):
        if not integration.credentials:
            raise Exception("No credentials found")
        
        creds = json.loads(decrypt_text(integration.credentials) if isinstance(integration.credentials, str) else json.dumps(integration.credentials))
        return creds.get("email"), creds.get("app_password")

    def _check_permission(self, integration: Integration, permission: str) -> bool:
        if not integration.settings:
            return False
        settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
        return settings.get(permission, False)

    # --- EMAIL METHODS (IMAP/SMTP) ---

    def list_emails(self, workspace_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "icloud_mailbox")
        if not integration:
            raise Exception("iCloud Mail integration not found")
        
        if not self._check_permission(integration, "can_read_emails"):
            raise Exception("Permission denied: Cannot read emails")

        user, password = self._get_credentials(integration)
        
        try:
            # Connect to iCloud IMAP
            mail = imaplib.IMAP4_SSL("imap.mail.me.com")
            mail.login(user, password)
            mail.select("inbox")

            # Search for all emails
            status, messages = mail.search(None, "ALL")
            mail_ids = messages[0].split()
            
            # Get latest 'limit' emails
            latest_ids = mail_ids[-limit:]
            
            emails = []
            for i in reversed(latest_ids):
                status, msg_data = mail.fetch(i, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")
                        
                        from_ = msg.get("From")
                        date_ = msg.get("Date")
                        
                        # Snippet extraction is hard without full parsing, skipping for list
                        
                        emails.append({
                            "id": str(int(i)), # IMAP ID
                            "subject": subject,
                            "from": from_,
                            "date": date_,
                            "snippet": "(Loading...)",
                            "provider": "icloud"
                        })
            
            mail.logout()
            return emails
        except Exception as e:
            logger.error(f"Error listing iCloud emails: {e}")
            raise e

    def read_email(self, workspace_id: int, email_id: str) -> Dict[str, Any]:
        integration = self._get_integration(workspace_id, "icloud_mailbox")
        if not integration:
            raise Exception("iCloud Mail integration not found")

        user, password = self._get_credentials(integration)

        try:
            mail = imaplib.IMAP4_SSL("imap.mail.me.com")
            mail.login(user, password)
            mail.select("inbox")

            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            email_body = ""
            msg = None
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                email_body += body
                    else:
                        content_type = msg.get_content_type()
                        body = msg.get_payload(decode=True).decode()
                        if content_type == "text/plain":
                            email_body = body

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            mail.logout()

            return {
                "id": email_id,
                "subject": subject,
                "from": msg.get("From"),
                "to": msg.get("To"),
                "date": msg.get("Date"),
                "body": email_body,
                "provider": "icloud"
            }
        except Exception as e:
            logger.error(f"Error reading iCloud email: {e}")
            raise e

    def send_email(self, workspace_id: int, to_email: str, subject: str, body: str) -> bool:
        integration = self._get_integration(workspace_id, "icloud_mailbox")
        if not integration:
            raise Exception("iCloud Mail integration not found")

        if not self._check_permission(integration, "can_send_emails"):
            raise Exception("Permission denied: Cannot send emails")

        user, password = self._get_credentials(integration)

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = user
            msg['To'] = to_email

            server = smtplib.SMTP_SSL("smtp.mail.me.com", 587)
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Error sending iCloud email: {e}")
            # Try port 465 (SSL) if 587 (TLS) fails
            try:
                server = smtplib.SMTP_SSL("smtp.mail.me.com", 465)
                server.login(user, password)
                server.sendmail(user, to_email, msg.as_string())
                server.quit()
                return True
            except Exception as e2:
                 logger.error(f"Error sending iCloud email (retry): {e2}")
                 raise e

    def search_emails(self, workspace_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # IMAP search is complex, generic text search
        # Returning list for now
        return self.list_emails(workspace_id, limit)

    # --- CALENDAR METHODS (CalDAV) ---
    
    def _get_caldav_client(self, integration):
        user, password = self._get_credentials(integration)
        # iCloud CalDAV URL
        url = "https://caldav.icloud.com/"
        client = caldav.DAVClient(url, username=user, password=password)
        return client

    def list_events(self, workspace_id: int, start_dt, end_dt) -> List[Dict[str, Any]]:
        integration = self._get_integration(workspace_id, "icloud_calendar")
        if not integration:
            # Fallback check for mailbox integration that might have calendar enabled?
            # For now, stick to specific provider type
            return []
            
        if not self._check_permission(integration, "can_view_events"):
            return []
            
        try:
            client = self._get_caldav_client(integration)
            principal = client.principal()
            calendars = principal.calendars()
            
            events_list = []
            if calendars:
                # Use primary calendar
                calendar = calendars[0] 
                results = calendar.date_search(start_dt, end_dt)
                
                for event in results:
                    try:
                        event.load()
                        vevent = event.instance.vevent
                        
                        summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "No Title"
                        uid = str(vevent.uid.value) if hasattr(vevent, 'uid') else str(event.url)
                        
                        dtstart = vevent.dtstart.value
                        dtend = vevent.dtend.value
                        
                        # Handle datetime vs date
                        start_str = dtstart.isoformat() if hasattr(dtstart, 'isoformat') else str(dtstart)
                        end_str = dtend.isoformat() if hasattr(dtend, 'isoformat') else str(dtend)
                        
                        desc = str(vevent.description.value) if hasattr(vevent, 'description') else ""
                        
                        events_list.append({
                            "id": uid,
                            "title": summary,
                            "start": start_str,
                            "end": end_str,
                            "description": desc,
                            "provider": "icloud_calendar"
                        })
                    except Exception as ev_err:
                        logger.error(f"Error parsing iCloud event: {ev_err}")
                        continue
                        
            return events_list
        except Exception as e:
            logger.error(f"Error listing iCloud events: {e}")
            return []
    
    def create_event(self, workspace_id: int, title: str, start_dt, end_dt, description: str = "") -> Dict[str, Any]:
        integration = self._get_integration(workspace_id, "icloud_calendar")
        if not integration:
            raise Exception("iCloud Calendar integration not found")
            
        if not self._check_permission(integration, "can_create_events"):
            raise Exception("Permission denied: Cannot create events")
            
        try:
            client = self._get_caldav_client(integration)
            principal = client.principal()
            calendars = principal.calendars()
            
            if not calendars:
                raise Exception("No iCloud calendars found")
                
            calendar = calendars[0]
            
            event = calendar.save_event(
                dtstart=start_dt,
                dtend=end_dt,
                summary=title,
                description=description
            )
            
            # Reload to get properties
            event.load()
            vevent = event.instance.vevent
            uid = str(vevent.uid.value)
            
            return {
                "id": uid,
                "title": title,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "provider": "icloud_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            logger.error(f"Error creating iCloud event: {e}")
            raise e

    def get_event(self, workspace_id: int, event_id: str) -> Optional[Dict[str, Any]]:
        # Complex to fetch by UID directly without search in CalDAV sometimes
        # But we can try searching by UID if supported or iterate
        # Optimization: Listing today +/- range is better?
        # Converting UID to URL is hard without cache.
        # For now, returning None as specialized UID lookup is expensive/tricky in generic CalDAV
        # Or implementing a search by UID
        return None 
        
    def update_event(self, workspace_id: int, event_id: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("iCloud update not yet supported")
        
    def delete_event(self, workspace_id: int, event_id: str) -> bool:
        raise NotImplementedError("iCloud delete not yet supported")
