from livekit.agents import llm
from datetime import datetime, timedelta
import random

class CalendarMixin:
    @llm.function_tool(description="List calendar appointments for a specific date.")
    async def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None):
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required."
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        db = SessionLocal()
        try:
            service = CalendarService(db)
            start_dt = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
            end_dt = start_dt + timedelta(days=1 if date else 7)
            events = service.list_events(self.workspace_id, start_dt, end_dt)
            # ... Verification logic ...
            return str(events)
        except Exception as e:
            return f"Error listing appointments: {str(e)}"
        finally: db.close()

    @llm.function_tool(description="Get available time slots for a specific date.")
    async def get_availability(self, date: str = None):
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        db = SessionLocal()
        try:
            service = CalendarService(db)
            slots = service.get_availability(self.workspace_id, datetime.strptime(date, "%Y-%m-%d") if date else datetime.now())
            return "\n".join(slots) if slots else "No availability."
        except Exception as e:
            return f"Error getting availability: {str(e)}"
        finally: db.close()

    @llm.function_tool(description="Create a new calendar appointment.")
    async def create_appointment(self, title: str, start_time: str, duration_minutes: int = 60, attendee_name: str = None, attendee_email: str = None, attendee_phone: str = None):
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        db = SessionLocal()
        try:
            service = CalendarService(db)
            event = service.create_event(self.workspace_id, title, datetime.fromisoformat(start_time), duration_minutes, attendee_name, attendee_email, attendee_phone)
            return f"Appointment created: {event.get('id')}"
        except Exception as e:
            return f"Error creating appointment: {str(e)}"
        finally: db.close()

    @llm.function_tool(description="Cancel an appointment.")
    async def cancel_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str):
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        db = SessionLocal()
        try:
            service = CalendarService(db)
            success = service.delete_event(self.workspace_id, appointment_id)
            return "Cancelled successfully." if success else "Failed to cancel."
        except Exception as e:
            return f"Error cancelling appointment: {str(e)}"
        finally: db.close()
