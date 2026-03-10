from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models_db import Integration
from backend.security import decrypt_text
import json

class CalendarService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int, provider: str) -> Optional[Integration]:
        print(f"DEBUG: Getting integration for workspace {workspace_id}, provider {provider}")
        integ = self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.provider == provider,
            Integration.is_active == True
        ).first()
        print(f"DEBUG: Integration found: {integ is not None}")
        return integ

    def _check_permission(self, integration: Integration, permission_type: str) -> bool:
        """
        Check if the integration has the specified permission enabled.
        permission_type: 'view', 'edit', or 'delete'
        Returns True if permission is granted, False otherwise.
        """
        if not integration or not integration.settings:
            return False
        
        try:
            settings = json.loads(integration.settings)
            permission_key = f"can_{permission_type}_own_events"
            # Default to True to allow legacy integrations or those without strict settings to work
            # The real security is handled by the OAuth scope and token validity
            has_permission = settings.get(permission_key, True)
            
            if not has_permission:
                print(f"Permission denied: {permission_type} for workspace {integration.workspace_id}")
            
            return has_permission
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False


    def list_events(self, workspace_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        events = []
        
        # Check Google Calendar
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ:
            if self._check_permission(google_integ, "view"):
                try:
                    fetched = self._fetch_google_events(google_integ, start_time, end_time)
                    events.extend(fetched)
                except Exception as e:
                    print(f"Error fetching Google events: {e}")

        # Check Outlook Calendar
        from backend.services.outlook_service import OutlookService
        outlook_service = OutlookService(self.db)
        # Note: OutlookService checks permissions internally, but uses 'outlook_calendar' provider name
        # We need to call list_events on it.
        try:
            outlook_events = outlook_service.list_events(workspace_id, start_time, end_time)
            events.extend(outlook_events)
        except Exception as e:
            print(f"Error fetching Outlook events: {e}")

        # Check iCloud Calendar
        from backend.services.icloud_service import ICloudService
        icloud_service = ICloudService(self.db)
        try:
            icloud_events = icloud_service.list_events(workspace_id, start_time, end_time)
            events.extend(icloud_events)
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"Error fetching iCloud events: {e}")
            
        return events

    def get_event(self, workspace_id: int, event_id: str) -> Optional[Dict[str, Any]]:
        # Check Google first
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ:
            try:
                service = self._get_google_service(google_integ)
                event = service.events().get(calendarId='primary', eventId=event_id).execute()
                return {
                    "id": event['id'],
                    "title": event.get('summary', 'No Title'),
                    "start": event['start'].get('dateTime', event['start'].get('date')),
                    "end": event['end'].get('dateTime', event['end'].get('date')),
                    "provider": "google_calendar",
                    "description": event.get('description', '')
                }
            except:
                pass # Try others
        
        # Check Outlook
        from backend.services.outlook_service import OutlookService
        outlook_service = OutlookService(self.db)
        try:
            event = outlook_service.get_event(workspace_id, event_id)
            if event:
                return event
        except Exception as e: 
            print(f"Error getting Outlook event: {e}")
            pass
            
        return None

    def create_event(self, workspace_id: int, title: str, start_time: datetime, end_time: datetime, description: str = "", attendees: list[str] = None) -> Dict[str, Any]:
        existing_events = self.list_events(workspace_id, start_time, end_time)
        if existing_events:
            conflict = existing_events[0]
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Toronto")
            display_start = start_time.astimezone(tz) if start_time.tzinfo else start_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
            display_end = end_time.astimezone(tz) if end_time.tzinfo else end_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
            raise Exception(f"Double Booking Detected: Time slot {display_start.strftime('%I:%M %p')} - {display_end.strftime('%I:%M %p')} conflicts with existing appointment '{conflict.get('title', 'Busy')}'.")

        # Prioritize Google -> Outlook -> iCloud
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ and self._check_permission(google_integ, "create"):
             return self._create_google_event(google_integ, title, start_time, end_time, description, attendees)

        # Outlook
        from backend.services.outlook_service import OutlookService
        outlook_service = OutlookService(self.db)
        try:
            # Check if active
            if outlook_service._get_integration(workspace_id, "outlook_calendar"):
                return outlook_service.create_event(workspace_id, title, start_time, end_time, description)
        except Exception as e:
            if "not found" not in str(e):
                print(f"Error creating Outlook event: {e}")
        
        # iCloud
        from backend.services.icloud_service import ICloudService
        icloud_service = ICloudService(self.db)
        try:
             if icloud_service._get_integration(workspace_id, "icloud_calendar"):
                 return icloud_service.create_event(workspace_id, title, start_time, end_time, description)
        except Exception as e:
             if "not found" not in str(e):
                print(f"Error creating iCloud event: {e}")
        
        raise Exception("No active calendar integration found")

    def update_event(self, workspace_id: int, event_id: str, start_time: datetime = None, end_time: datetime = None, title: str = None, description: str = None) -> Dict[str, Any]:
        # Check conflicts
        if start_time and end_time:
            existing_events = self.list_events(workspace_id, start_time, end_time)
            for event in existing_events:
                if event['id'] != event_id:
                     raise Exception(f"Double Booking Detected: Time slot conflicts with '{event.get('title', 'Busy')}'")

        # Try Google
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ:
            try:
                if self._check_permission(google_integ, "edit"):
                     return self._update_google_event(google_integ, event_id, start_time, end_time, title, description)
            except:
                pass

        # Try Outlook
        from backend.services.outlook_service import OutlookService
        outlook_service = OutlookService(self.db)
        try:
            if outlook_service._get_integration(workspace_id, "outlook_calendar"):
                 return outlook_service.update_event(workspace_id, event_id, start_time, end_time, title, description)
        except Exception as e:
             print(f"Error updating Outlook event: {e}")

        raise Exception("Event not found or update not supported for this provider")

    def delete_event(self, workspace_id: int, event_id: str) -> bool:
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ:
            try:
                 if self._check_permission(google_integ, "delete"):
                     return self._delete_google_event(google_integ, event_id)
            except:
                pass
        
        # Outlook delete
        from backend.services.outlook_service import OutlookService
        outlook_service = OutlookService(self.db)
        try:
            if outlook_service.delete_event(workspace_id, event_id):
                return True
        except:
            pass
            
        return False


    def verify_appointment_ownership(self, event: Dict[str, Any], verify_name: str, verify_phone: str, verify_email: str) -> (bool, str):
        """
        Verify that the provided identity matches the appointment owner details stored in the event description.
        Returns: (is_verified: bool, message: str)
        """
        description = event.get('description', '')
        
        stored_name = None
        stored_phone = None
        stored_email = None
        
        # Parse PII from description (Case insensitive scan)
        for line in description.split('\n'):
            line_lower = line.lower().strip()
            if line_lower.startswith('customer name:'):
                stored_name = line.split(':', 1)[1].strip()
            elif line_lower.startswith('phone:'):
                stored_phone = line.split(':', 1)[1].strip()
            elif line_lower.startswith('email:'):
                stored_email = line.split(':', 1)[1].strip()
        
        # 1. Check Email Match (if stored)
        if stored_email and verify_email:
            if stored_email.lower() == verify_email.lower():
                return True, "Email verified."
        
        # 2. Check Phone Match (if stored)
        if stored_phone and verify_phone:
            # Normalize digits
            stored_digits = "".join(filter(str.isdigit, stored_phone))
            verify_digits = "".join(filter(str.isdigit, verify_phone))
            if stored_digits and verify_digits and stored_digits == verify_digits:
                return True, "Phone verified."
                
        # 3. Check Name (Weak verification, only if others missing? No, insecure. 
        # But if we found NO contact info, maybe the event was created manually?)
        if not stored_email and not stored_phone:
            return False, "This appointment has no contact details on file. Please contact support manually."
            
        return False, "Identity does not match appointment records."

    def _get_google_service(self, integration):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds_data = json.loads(decrypt_text(integration.credentials))
        
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes")
        )
        
        return build('calendar', 'v3', credentials=creds)

    def _fetch_google_events(self, integration, start, end):
        try:
            service = self._get_google_service(integration)
            
            # Handle naive vs aware datetimes for Google API
            # Default to America/Toronto (EST) if naive
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Toronto")
            
            if start.tzinfo is None:
                start = start.replace(tzinfo=tz)
            if end.tzinfo is None:
                end = end.replace(tzinfo=tz)
                
            time_min = start.isoformat()
            time_max = end.isoformat()

            print(f"DEBUG: Fetching Google Events from {time_min} to {time_max}")

            events_result = service.events().list(
                calendarId='primary', 
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "id": event['id'],
                    "title": event.get('summary', 'No Title'),
                    "start": event['start'].get('dateTime', event['start'].get('date')),
                    "end": event['end'].get('dateTime', event['end'].get('date')),
                    "provider": "google_calendar",
                    "description": event.get('description', '')
                })
                
            return formatted_events
        except Exception as e:
            print(f"Error fetching Google events: {e}")
            return []

    def _fetch_exchange_events(self, integration, start, end):
        # In reality: Use exchangelib
        return [
            {
                "id": "exch_456",
                "title": "Follow-up (Exchange)",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "provider": "exchange"
            }
        ]

    def _create_google_event(self, integration, title, start, end, description, attendees=None):
        try:
            service = self._get_google_service(integration)
            
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Toronto")
            
            if start.tzinfo is None:
                start = start.replace(tzinfo=tz)
            if end.tzinfo is None:
                end = end.replace(tzinfo=tz)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': 'America/Toronto',
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': 'America/Toronto',
                },
            }

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            print(f"DEBUG: Creating Google Event: {event}")
            event = service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "id": event['id'],
                "title": event.get('summary'),
                "start": event['start'].get('dateTime'),
                "end": event['end'].get('dateTime'),
                "provider": "google_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            print(f"Error creating Google event: {e}")
            raise e

    def _create_exchange_event(self, integration, title, start, end, description, attendees=None):
        return {
            "id": "exch_new_012",
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "provider": "exchange",
            "status": "confirmed"
        }

    def _update_google_event(self, integration, event_id, start=None, end=None, title=None, description=None):
        try:
            service = self._get_google_service(integration)
            
            # First fetch the existing event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            
            if start and end:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("America/Toronto")
                if start.tzinfo is None:
                    start = start.replace(tzinfo=tz)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=tz)
                    
                event['start'] = {
                    'dateTime': start.isoformat(),
                    'timeZone': 'America/Toronto',
                }
                event['end'] = {
                    'dateTime': end.isoformat(),
                    'timeZone': 'America/Toronto',
                }
            
            print(f"DEBUG: Updating Google Event: {event_id}")
            updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            
            return {
                "id": updated_event['id'],
                "title": updated_event.get('summary'),
                "start": updated_event['start'].get('dateTime'),
                "end": updated_event['end'].get('dateTime'),
                "provider": "google_calendar",
                "status": "confirmed"
            }
        except Exception as e:
            print(f"Error updating Google event: {e}")
            raise e

    def _delete_google_event(self, integration, event_id):
        try:
            service = self._get_google_service(integration)
            print(f"DEBUG: Deleting Google Event: {event_id}")
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting Google event: {e}")
            raise e

    def _update_exchange_event(self, integration, event_id, start=None, end=None, title=None, description=None):
        # Mock implementation
        return {
            "id": event_id,
            "title": title or "Updated Event",
            "start": start.isoformat() if start else datetime.now().isoformat(),
            "end": end.isoformat() if end else datetime.now().isoformat(),
            "provider": "exchange",
            "status": "confirmed"
        }

    def get_availability(self, workspace_id: int, date: datetime) -> List[str]:
        """
        Calculate available time slots for a given date based on business hours and existing events.
        Returns a list of formatted strings representing free slots (e.g., "09:00 AM - 10:00 AM").
        """
        from backend.models_db import Workspace
        from datetime import timedelta
        import json

        # 1. Get Business Hours
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace or not workspace.business_hours:
            # Default to 9 AM - 5 PM if not configured
            print(f"DEBUG get_availability: No business hours configured, using default 9 AM - 5 PM")
            open_time = datetime.strptime("09:00", "%H:%M").time()
            close_time = datetime.strptime("17:00", "%H:%M").time()
        else:
            try:
                business_hours = json.loads(workspace.business_hours)
            except:
                # If not JSON, treat the wide string as a simple schedule applicable to all days
                # This handles cases where the frontend saves a plain string like "9:00 AM - 5:00 PM"
                print(f"DEBUG get_availability: Business hours not JSON, treating as global string: {workspace.business_hours}")
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                business_hours = {day: workspace.business_hours for day in days}
            
            # Remove the 'else' block indentation for the following logic so it runs for both JSON and fallback cases
            day_name = date.strftime("%A")  # Full day name like "Monday", "Tuesday"
            print(f"DEBUG get_availability: Looking for day '{day_name}' in business_hours: {business_hours}")
            
            # Try exact match first (case-sensitive)
            hours = business_hours.get(day_name)
            
            # If not found, try lowercase
            if not hours:
                day_name_lower = day_name.lower()
                hours = business_hours.get(day_name_lower)
            
            print(f"DEBUG get_availability: Found hours for {day_name}: {hours}")
            
            # If still not found, use default hours
            if not hours:
                print(f"DEBUG get_availability: No hours for {day_name}, using default 9 AM - 5 PM")
                open_time = datetime.strptime("09:00", "%H:%M").time()
                close_time = datetime.strptime("17:00", "%H:%M").time()
            else:
                # Handle different formats
                open_str = None
                close_str = None
                
                # Format 1: String like "11:00 am - 7:00 pm" or "Closed"
                if isinstance(hours, str):
                    if hours.lower() == "closed":
                        return [f"Closed on {day_name}"]
                    
                    # Parse "11:00 am - 7:00 pm" format
                    if " - " in hours:
                        try:
                            parts = hours.split(" - ")
                            open_str = parts[0].strip()
                            close_str = parts[1].strip()
                            
                            print(f"DEBUG get_availability: Parsing times - open: '{open_str}', close: '{close_str}'")
                            
                            # Convert 12-hour format to 24-hour format
                            open_time = datetime.strptime(open_str, "%I:%M %p").time()
                            close_time = datetime.strptime(close_str, "%I:%M %p").time()
                            
                            print(f"DEBUG get_availability: Parsed times - open: {open_time}, close: {close_time}")
                        except ValueError as e:
                            print(f"DEBUG get_availability: ValueError parsing times: {e}, using default")
                            open_time = datetime.strptime("09:00", "%H:%M").time()
                            close_time = datetime.strptime("17:00", "%H:%M").time()
                    else:
                        # Invalid format, use default
                        print(f"DEBUG get_availability: Invalid format, using default")
                        open_time = datetime.strptime("09:00", "%H:%M").time()
                        close_time = datetime.strptime("17:00", "%H:%M").time()
                
                # Format 2: Dict like {"open": "11:00", "close": "19:00"}
                elif isinstance(hours, dict):
                    if not hours.get("open") or not hours.get("close"):
                        return [f"Closed on {day_name}"]
                    
                    open_str = hours["open"]
                    close_str = hours["close"]
                    
                    try:
                        open_time = datetime.strptime(open_str, "%H:%M").time()
                        close_time = datetime.strptime(close_str, "%H:%M").time()
                    except ValueError:
                        # Invalid format, use default
                        print(f"DEBUG get_availability: Invalid time format, using default")
                        open_time = datetime.strptime("09:00", "%H:%M").time()
                        close_time = datetime.strptime("17:00", "%H:%M").time()
                else:
                    # Invalid format, use default
                    print(f"DEBUG get_availability: Invalid hours type, using default")
                    open_time = datetime.strptime("09:00", "%H:%M").time()
                    close_time = datetime.strptime("17:00", "%H:%M").time()


        # 2. Get Existing Events

        start_of_day = date.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)
        end_of_day = date.replace(hour=close_time.hour, minute=close_time.minute, second=0, microsecond=0)
        
        # Fetch events for the whole day to be safe
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = date.replace(hour=23, minute=59, second=59)
        
        events = self.list_events(workspace_id, day_start, day_end)

        # 3. Calculate Free Slots (Hourly chunks for simplicity)
        free_slots = []
        current_slot = start_of_day
        
        while current_slot < end_of_day:
            slot_end = current_slot + timedelta(hours=1)
            if slot_end > end_of_day:
                break
            
            # Check for overlap
            is_busy = False
            for event in events:
                # Parse event times (handle ISO strings or datetime objects)
                evt_start = event['start']
                evt_end = event['end']
                
                if isinstance(evt_start, str):
                    evt_start = datetime.fromisoformat(evt_start)
                if isinstance(evt_end, str):
                    evt_end = datetime.fromisoformat(evt_end)
                
                # Normalize timezones if needed (naive vs aware comparison)
                if evt_start.tzinfo and not current_slot.tzinfo:
                     # Assume current_slot is in the same TZ as event or local
                     # For simplicity, strip TZ from event or add to current
                     # Wait, we need to compare apples to apples.
                     # If event is aware, convert current to aware or event to naive.
                     # Here we strip TZ for safety if mixed
                     evt_start = evt_start.replace(tzinfo=None)
                if evt_end.tzinfo and not slot_end.tzinfo:
                     evt_end = evt_end.replace(tzinfo=None)

                # Overlap logic: (StartA < EndB) and (EndA > StartB)
                if current_slot < evt_end and slot_end > evt_start:
                    is_busy = True
                    break
            
            if not is_busy:
                free_slots.append(f"{current_slot.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}")
            
            current_slot = slot_end

        if not free_slots:
            return ["No available slots for this date."]
            
        return free_slots
