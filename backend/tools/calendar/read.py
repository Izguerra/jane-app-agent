import json
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.services.calendar_service import CalendarService
from .verification import CalendarVerification

class CalendarReadTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None) -> str:
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before showing appointments."
        
        db = SessionLocal()
        try:
            if not CalendarVerification.check_permission(db, self.workspace_id, "view"):
                return "Permission denied: The workspace settings do not allow viewing calendar events."
            
            service = CalendarService(db)
            if date:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=1)
            else:
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(days=7)
            
            events = service.list_events(self.workspace_id, start_dt, end_dt)
            if not events:
                return "No appointments found for this date."
            
            user_events = []
            for event in events:
                description = event.get('description', '')
                stored_email = None
                stored_phone = None
                
                for line in description.split('\n'):
                    line_lower = line.lower().strip()
                    if line_lower.startswith('phone:'):
                        stored_phone = line.split(':', 1)[1].strip()
                    elif line_lower.startswith('email:'):
                        stored_email = line.split(':', 1)[1].strip()
                
                email_match = verify_email and stored_email and verify_email.lower() == stored_email.lower()
                v_p_digits = "".join(filter(str.isdigit, verify_phone)) if verify_phone else ""
                s_p_digits = "".join(filter(str.isdigit, stored_phone)) if stored_phone else ""
                phone_match = v_p_digits and s_p_digits and v_p_digits == s_p_digits
                
                if email_match or phone_match:
                    clean_lines = [l for l in description.split('\n') if not l.startswith(('Customer Name:', 'Phone:', 'Email:', 'Appointment ID:'))]
                    safe_event = event.copy()
                    safe_event['description'] = "\n".join(clean_lines).strip()
                    user_events.append(safe_event)
            
            if not user_events:
                return f"No appointments found for {verify_name} in range {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}."
            
            return f"Search Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}\n\n{json.dumps(user_events, default=str, indent=2)}"
        except Exception as e:
            return f"Error listing appointments: {str(e)}"
        finally:
            db.close()

    def get_availability(self, date: str = None) -> str:
        db = SessionLocal()
        try:
            if not CalendarVerification.check_permission(db, self.workspace_id, "view"):
                return "Permission denied: The workspace settings do not allow viewing calendar availability."
            
            service = CalendarService(db)
            target_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
            slots = service.get_availability(self.workspace_id, target_date)
            
            if not slots:
                return "No availability information available."
            
            return f"Available slots for {target_date.strftime('%A, %B %d, %Y')}:\n" + "\n".join([f"- {slot}" for slot in slots])
        except Exception as e:
            return f"Error getting availability: {str(e)}"
        finally:
            db.close()
