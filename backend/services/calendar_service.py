from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from backend.models_db import Integration
from .calendar.google import GoogleCalendarProvider
from .calendar.availability import CalendarAvailability

class CalendarService:
    def __init__(self, db_session):
        self.db = db_session

    def _get_integration(self, workspace_id: int, provider: str) -> Optional[Integration]:
        return self.db.query(Integration).filter(
            Integration.workspace_id == workspace_id, Integration.provider == provider, Integration.is_active == True
        ).first()

    def _check_permission(self, integration: Integration, permission_type: str) -> bool:
        if not integration or not integration.settings: return False
        try:
            settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
            return settings.get(f"can_{permission_type}_own_events", True)
        except: return False

    def list_events(self, workspace_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        events = []
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ and self._check_permission(google_integ, "view"):
            events.extend(GoogleCalendarProvider.fetch_events(google_integ, start_time, end_time))

        from backend.services.outlook_service import OutlookService
        try: events.extend(OutlookService(self.db).list_events(workspace_id, start_time, end_time))
        except: pass

        from backend.services.icloud_service import ICloudService
        try: events.extend(ICloudService(self.db).list_events(workspace_id, start_time, end_time))
        except: pass
            
        return events

    def get_event(self, workspace_id: int, event_id: str) -> Optional[Dict[str, Any]]:
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ:
            try:
                service = GoogleCalendarProvider.get_service(google_integ)
                e = service.events().get(calendarId='primary', eventId=event_id).execute()
                return {"id": e['id'], "title": e.get('summary', 'No Title'), "start": e['start'].get('dateTime', e['start'].get('date')), "end": e['end'].get('dateTime', e['end'].get('date')), "provider": "google_calendar", "description": e.get('description', '')}
            except: pass
        
        from backend.services.outlook_service import OutlookService
        try:
            event = OutlookService(self.db).get_event(workspace_id, event_id)
            if event: return event
        except: pass
        return None

    def create_event(self, workspace_id: int, title: str, start_time: datetime, end_time: datetime, description: str = "", attendees: list[str] = None) -> Dict[str, Any]:
        existing = self.list_events(workspace_id, start_time, end_time)
        if existing: raise Exception(f"Double Booking Detected: Time slot conflicts with '{existing[0].get('title', 'Busy')}'.")

        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ and self._check_permission(google_integ, "create"):
             return GoogleCalendarProvider.create_event(google_integ, title, start_time, end_time, description, attendees)

        from backend.services.outlook_service import OutlookService
        outlook = OutlookService(self.db)
        if outlook._get_integration(workspace_id, "outlook_calendar"): return outlook.create_event(workspace_id, title, start_time, end_time, description)
        
        from backend.services.icloud_service import ICloudService
        icloud = ICloudService(self.db)
        if icloud._get_integration(workspace_id, "icloud_calendar"): return icloud.create_event(workspace_id, title, start_time, end_time, description)
        
        raise Exception("No active calendar integration found")

    def update_event(self, workspace_id: int, event_id: str, start_time: datetime = None, end_time: datetime = None, title: str = None, description: str = None) -> Dict[str, Any]:
        if start_time and end_time:
            existing = self.list_events(workspace_id, start_time, end_time)
            if any(e['id'] != event_id for e in existing): raise Exception("Double Booking Detected.")

        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ and self._check_permission(google_integ, "edit"):
            try: return GoogleCalendarProvider.update_event(google_integ, event_id, start_time, end_time, title, description)
            except: pass

        from backend.services.outlook_service import OutlookService
        outlook = OutlookService(self.db)
        if outlook._get_integration(workspace_id, "outlook_calendar"): return outlook.update_event(workspace_id, event_id, start_time, end_time, title, description)

        raise Exception("Event not found or update not supported")

    def delete_event(self, workspace_id: int, event_id: str) -> bool:
        google_integ = self._get_integration(workspace_id, "google_calendar")
        if google_integ and self._check_permission(google_integ, "delete"):
            try: return GoogleCalendarProvider.delete_event(google_integ, event_id)
            except: pass
        
        from backend.services.outlook_service import OutlookService
        try: return OutlookService(self.db).delete_event(workspace_id, event_id)
        except: return False

    def verify_appointment_ownership(self, event: Dict[str, Any], verify_name: str, verify_phone: str, verify_email: str) -> (bool, str):
        desc = event.get('description', '')
        s_email, s_phone = None, None
        for line in desc.split('\n'):
            l = line.lower().strip()
            if l.startswith('phone:'): s_phone = line.split(':', 1)[1].strip()
            elif l.startswith('email:'): s_email = line.split(':', 1)[1].strip()
        
        if s_email and verify_email and s_email.lower() == verify_email.lower(): return True, "Email verified."
        if s_phone and verify_phone:
            s_d, v_d = "".join(filter(str.isdigit, s_phone)), "".join(filter(str.isdigit, verify_phone))
            if s_d and v_d and s_d == v_d: return True, "Phone verified."
                
        if not s_email and not s_phone: return False, "No contact details on file."
        return False, "Identity mismatch."

    def get_availability(self, workspace_id: int, date: datetime) -> List[str]:
        return CalendarAvailability.get_free_slots(self.db, workspace_id, date, self.list_events)
