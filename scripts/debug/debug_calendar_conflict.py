
import logging
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.services.calendar_service import CalendarService
from zoneinfo import ZoneInfo

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_conflict():
    db = SessionLocal()
    try:
        service = CalendarService(db)
        
        # We know there is an appointment at 2026-01-02 18:00:00 UTC (1 PM EST)
        # confirmed in previous turn.
        
        # Try to create an overlapping appointment
        # Target: 2026-01-02 13:00 EST (to 14:00 EST)
        tz = ZoneInfo("America/New_York")
        start_time = datetime(2026, 1, 2, 13, 0, 0, tzinfo=tz) 
        end_time = start_time + timedelta(hours=1)
        
        workspace_id = "ws_primary" # Assuming this is the ID, or I should fetch it
        # Actually, let's fetch the first workspace to be safe
        from backend.models_db import Workspace, Integration
        workspaces = db.query(Workspace).all()
        print(f"Found {len(workspaces)} workspaces:")
        target_ws_id = None
        
        for ws in workspaces:
            integs = db.query(Integration).filter(Integration.workspace_id == ws.id).all()
            integ_summary = [f"{i.provider}(active={i.is_active})" for i in integs]
            print(f" - {ws.name} (ID: {ws.id}) | Integs: {integ_summary}")
            
            # Prefer one with google_calendar
            for i in integs:
                if i.provider == 'google_calendar' and i.is_active:
                    target_ws_id = ws.id
        
        if not target_ws_id:
             print("No workspace with active Google Calendar found. Using first available.")
             if workspaces:
                 target_ws_id = workspaces[0].id
             else:
                 print("No workspaces at all!")
                 return

        workspace_id = target_ws_id
        print(f"Using Workspace ID: {workspace_id}")

        print(f"Attempting to create conflicting event: {start_time} - {end_time}")
        
        try:
            result = service.create_event(
                workspace_id=workspace_id,
                title="Debug Conflict Appointment",
                start_time=start_time,
                end_time=end_time,
                description="Testing double booking",
                attendees=["test@example.com"]
            )
            print("Event created unexpectedly (No conflict detected):", result)
        except Exception as e:
            print("\n---------------------------------------------------")
            print("CAUGHT EXCEPTION (This is what we want if it's 'Double Booking'):")
            print(f"Type: {type(e)}")
            print(f"Message: {e}")
            import traceback
            traceback.print_exc()
            print("---------------------------------------------------\n")

    except Exception as e:
        print(f"Setup/Outer Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_conflict()
