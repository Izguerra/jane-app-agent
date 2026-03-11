
import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd()))

from backend.database import SessionLocal
from backend.tools.calendar_tools import CalendarTools
from backend.models_db import Integration, Workspace, Appointment, Customer

def run_verification():
    print("=== STARTING CALENDAR TOOL VERIFICATION ===")
    db = SessionLocal()
    try:
        # 1. Setup Test Workspace & Integration
        print("\n[Step 1] Setting up Test Environment...")
        workspace = db.query(Workspace).first()
        if not workspace:
            print("ERROR: No workspace found. Cannot test.")
            return

        workspace_id = workspace.id
        print(f"Using Workspace ID: {workspace_id}")

        # Ensure Google Calendar Integration exists with ALL permissions
        integ = db.query(Integration).filter(
            Integration.workspace_id == workspace_id, 
            Integration.provider == 'google_calendar'
        ).first()

        full_perms = {
            "can_view_own_events": True,
            "can_edit_own_events": True,
            "can_delete_own_events": True
        }

        if not integ:
            print("Creating Mock Google Integration...")
            import uuid
            integ = Integration(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                provider='google_calendar',
                is_active=True,
                credentials=json.dumps({"mock": "true"}), # Mock creds will fail actual Google calls, but we want to test logic/flow
                settings=json.dumps(full_perms)
            )
            db.add(integ)
            db.commit()
        else:
            print("Updating existing integration permissions to TRUE...")
            integ.settings = json.dumps(full_perms)
            integ.is_active = True
            db.commit()

        # Mock the CalendarService to avoid real Google API calls failing
        # We will monkeypatch CalendarService inside CalendarTools context if possible
        # Or we just accept that 'create_event' will fail at the API level but we want to check logic BEFORE that
        # Actually, the tool logic commits DB *after* API success usually.
        # So we really need the API call to mock-succeed.
        
        # Let's Patch CalendarService locally
        from backend.services.calendar_service import CalendarService
        
        def mock_create_event(self, ws_id, title, start, end, desc, attendees):
            print(f"  [MOCK API] creating event '{title}'")
            return {
                "id": "mock_gcal_id_123",
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "provider": "google_calendar"
            }
        
        def mock_update_event(self, ws_id, evt_id, start_time=None, end_time=None, title=None, description=None):
             print(f"  [MOCK API] updating event '{evt_id}'")
             return {
                "id": evt_id,
                "title": title or "Updated Title",
                "start": start_time.isoformat() if start_time else datetime.now().isoformat(),
                "end": end_time.isoformat() if end_time else datetime.now().isoformat(),
                "provider": "google_calendar"
             }

        def mock_delete_event(self, ws_id, evt_id):
             print(f"  [MOCK API] deleting event '{evt_id}'")
             return True

        def mock_get_event(self, ws_id, evt_id):
            return {
                "id": evt_id,
                "title": "Existing Event",
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(hours=1)).isoformat(),
                "description": "Appointment ID: mock_appt_id\nCustomer Name: Test User\nPhone: 5550001111\nEmail: test@test.com"
            }
            
        # Apply Mocks
        CalendarService.create_event = mock_create_event
        CalendarService.update_event = mock_update_event
        CalendarService.delete_event = mock_delete_event
        CalendarService.get_event = mock_get_event
        # Also need to mock verify_ownership inside CalendarService if it checks PII
        # But our tool does it? No the tool calls service.verify_appointment_ownership
        # Let's mock that too cause it might be strictly checking logic we don't want to assert on mock data
        # Actually, let's let it run if possible. verify_appointment_ownership likely parses description.
        # My mock_get_event includes PII key-values.
        
        tools = CalendarTools(workspace_id)

        # 2. Test Booking (Create)
        print("\n[Step 2] Testing create_appointment...")
        test_email = "verify_test@test.com"
        test_phone = "5550001111"
        test_name = "Verify TestUser"
        
        # Cleanup previous run
        exist_cust = db.query(Customer).filter(Customer.email == test_email).first()
        if exist_cust: db.delete(exist_cust)
        db.commit()

        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        result = tools.create_appointment(
            title="Verification Appt",
            start_time=start_time,
            attendee_name=test_name,
            attendee_email=test_email,
            attendee_phone=test_phone
        )
        print(f"Result: {result}")
        
        # Verify DB
        customer = db.query(Customer).filter(Customer.email == test_email).first()
        if customer:
            print("  [SUCCESS] Customer created in DB.")
        else:
            print("  [FAIL] Customer NOT created.")
            
        appt = db.query(Appointment).filter(Appointment.customer_email == test_email).first()
        if appt and appt.customer_id == customer.id:
             print(f"  [SUCCESS] Appointment created and linked to Customer ID {customer.id}")
             last_appt_id = appt.id
        else:
             print("  [FAIL] Appointment logic failed.")

        # 2b. Test Phone Normalization (Regression Test for "Orphaned Booking")
        print("\n[Step 2b] Testing Robust Phone Lookup (Duplication Fix)...")
        # Ensure we have a formatted number in DB
        customer.phone = "416-786-5786" # formatted
        db.commit()
        
        # Try to book with raw digits
        result_dup = tools.create_appointment(
            title="Duplication Test",
            start_time=(datetime.now() + timedelta(days=5)).isoformat(),
            attendee_name="Duplicate Attempt",
            attendee_email="diff@test.com", # Diff email to force phone lookup
            attendee_phone="4167865786" # Raw digits
        )
        print(f"Result: {result_dup}")
        
        # Check if a new customer was created or the old one reused
        dup_appt = db.query(Appointment).filter(Appointment.title == "Duplication Test").first()
        if dup_appt and dup_appt.customer_id == customer.id:
             print(f"  [SUCCESS] Phone lookup found existing customer {customer.id}. No duplicate created.")
        else:
             print(f"  [FAIL] Created duplicate/orphaned customer! Appt linked to: {dup_appt.customer_id if dup_appt else 'None'}")


        # 3. Test Editing (Date Change)
        print("\n[Step 3] Testing edit_appointment...")
        if appt:
            new_date = (datetime.now() + timedelta(days=2)).isoformat()
            res = tools.edit_appointment(
                appointment_id=last_appt_id,
                verify_name=test_name,
                verify_email=test_email,
                verify_phone=test_phone,
                new_start_time=new_date,
                new_title="Updated Verification Appt"
            )
            print(f"Result: {res}")
            
            db.refresh(appt)
            # Check DB update
            # Note: The tool updates appointment_date. Comparison might be naive vs aware.
            # Just check if title changed.
            if appt.title == "Updated Verification Appt":
                 print("  [SUCCESS] DB Title updated.")
            else:
                 print(f"  [FAIL] DB Title mismatch: {appt.title}")
                 
        # 4. Test Permissions (Deny)
        print("\n[Step 4] Testing Permission Denial...")
        integ = db.query(Integration).filter(Integration.provider == 'google_calendar').first()
        settings = json.loads(integ.settings)
        settings['can_delete_own_events'] = False # Deny delete
        integ.settings = json.dumps(settings)
        db.commit()
        
        res = tools.cancel_appointment(
            appointment_id="mock_gcal_id_123", # Using the ID our mock returned
            verify_name=test_name,
            verify_email=test_email,
            verify_phone=test_phone
        )
        print(f"Result: {res}")
        if "Permission denied" in res:
             print("  [SUCCESS] Permission check blocked cancellation.")
        else:
             print("  [FAIL] Permission check did NOT block.")
             
        # Re-enable for cleanup
        settings['can_delete_own_events'] = True
        integ.settings = json.dumps(settings)
        db.commit()
        
        # 5. Test Cancellation (Success)
        print("\n[Step 5] Testing cancel_appointment...")
        # We need to ensure the appt ID we pass matches what's in DB for the Sync to work
        # The tool does: local_appt = db.query(Appointment).filter((id==ID) | (calendar_event_id==ID)).first()
        # Our mock create returned ID "mock_gcal_id_123". The Appt record stored it in calendar_event_id.
        # So passing "mock_gcal_id_123" should work.
        
        res = tools.cancel_appointment(
            appointment_id="mock_gcal_id_123",
            verify_name=test_name,
            verify_email=test_email,
            verify_phone=test_phone
        )
        print(f"Result: {res}")
        
        db.refresh(appt)
        if appt.status == 'cancelled':
             print("  [SUCCESS] DB status updated to 'cancelled'.")
        else:
             print(f"  [FAIL] DB status mismatch: {appt.status}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_verification()
