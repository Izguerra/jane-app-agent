
import sys
import os
import json
from datetime import datetime
import traceback

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration
from backend.services.gmail_service import GmailService
from backend.services.outlook_service import OutlookService
from backend.services.icloud_service import ICloudService
from backend.services.google_drive_service import GoogleDriveService
from backend.services.calendar_service import CalendarService

def print_result(name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name}: {message}")

def verify_integrations(workspace_id):
    db = SessionLocal()
    print(f"\nVerifying Integrations for Workspace ID: {workspace_id}")
    print("="*60)
    
    try:
        integrations = db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.is_active == True
        ).all()
        
        if not integrations:
            print("⚠️  No active integrations found for this workspace.")
            print("   Please configure integrations via the dashboard first.")
            return

        providers = {i.provider for i in integrations}
        print(f"Found active providers: {', '.join(providers)}\n")

        # --- GMAIL ---
        if "gmail_mailbox" in providers:
            print(f"\n--- Testing Gmail Mailbox ---")
            try:
                service = GmailService(db)
                check_read = service._check_permission(service._get_integration(workspace_id, "gmail_mailbox"), "can_read_emails")
                
                if check_read:
                    emails = service.list_emails(workspace_id, limit=3)
                    print_result("List Emails", True, f"Retrieved {len(emails)} emails")
                    if emails:
                        detail = service.read_email(workspace_id, emails[0]['id'])
                        print_result("Read Email", True, f"Subject: {detail.get('subject')}")
                else:
                    print_result("List Emails", False, "Permission 'can_read_emails' disabled")
            except Exception as e:
                print_result("Gmail Mailbox", False, str(e))

        # --- OUTLOOK MAILBOX ---
        if "outlook_mailbox" in providers:
            print(f"\n--- Testing Outlook Mailbox ---")
            try:
                service = OutlookService(db)
                emails = service.list_emails(workspace_id, limit=3)
                print_result("List Emails", True, f"Retrieved {len(emails)} emails")
                if emails:
                    detail = service.read_email(workspace_id, emails[0]['id'])
                    print_result("Read Email", True, f"Subject: {detail.get('subject')}")
            except Exception as e:
                print_result("Outlook Mailbox", False, str(e))

        # --- OUTLOOK CALENDAR ---
        if "outlook_calendar" in providers:
            print(f"\n--- Testing Outlook Calendar ---")
            try:
                service = OutlookService(db)
                now = datetime.now()
                from datetime import timedelta
                events = service.list_events(workspace_id, now, now + timedelta(days=7))
                print_result("List Events", True, f"Retrieved {len(events)} events")
                
                # CRUD Test
                print("   > Attempting to create test event...")
                new_event = service.create_event(workspace_id, "Test Event Auto", now + timedelta(hours=1), now + timedelta(hours=2), "Created by verification script")
                print_result("Create Event", True, f"Created ID: {new_event['id']}")
                
                # Get
                fetched = service.get_event(workspace_id, new_event['id'])
                print_result("Get Event", True, f"Verified Title: {fetched['title']}")
                
                # Delete
                deleted = service.delete_event(workspace_id, new_event['id'])
                print_result("Delete Event", deleted, "Cleaned up test event")
                
            except Exception as e:
                print_result("Outlook Calendar", False, str(e))

        # --- ICLOUD MAILBOX ---
        if "icloud_mailbox" in providers:
            print(f"\n--- Testing iCloud Mailbox ---")
            try:
                service = ICloudService(db)
                emails = service.list_emails(workspace_id, limit=3)
                print_result("List Emails", True, f"Retrieved {len(emails)} emails")
            except Exception as e:
                print_result("iCloud Mailbox", False, str(e))

        # --- ICLOUD CALENDAR ---
        if "icloud_calendar" in providers:
            print(f"\n--- Testing iCloud Calendar ---")
            try:
                service = ICloudService(db)
                now = datetime.now()
                from datetime import timedelta
                events = service.list_events(workspace_id, now, now + timedelta(days=7))
                print_result("List Events", True, f"Retrieved {len(events)} events")
            except Exception as e:
                print_result("iCloud Calendar", False, str(e))

        # --- GOOGLE DRIVE ---
        if "google_drive" in providers:
            print(f"\n--- Testing Google Drive ---")
            try:
                service = GoogleDriveService(db)
                files = service.list_files(workspace_id, limit=3)
                print_result("List Files", True, f"Retrieved {len(files)} files")
                if files:
                    # Try reading metadata of first file
                    f = files[0]
                    print(f"   > File: {f['name']} ({f['mime_type']})")
            except Exception as e:
                print_result("Google Drive", False, str(e))

        # --- UNIFIED CALENDAR SERVICE ---
        print(f"\n--- Testing Unified Calendar Service ---")
        try:
            service = CalendarService(db)
            now = datetime.now()
            from datetime import timedelta
            # This should list from ALL connected providers
            events = service.list_events(workspace_id, now, now + timedelta(days=7))
            print_result("Unified List", True, f"Retrieved {len(events)} total events across providers")
            for evt in events[:3]:
                print(f"   > [{evt.get('provider')}] {evt.get('title')} ({evt.get('start')})")
        except Exception as e:
            print_result("Unified Calendar", False, str(e))

    except Exception as e:
        print(f"\n❌ Critical Script Error: {e}")
        traceback.print_exc()
    finally:
        db.close()
        print("\n" + "="*60)
        print("Verification Complete")

if __name__ == "__main__":
    # Default to 'template_workspace' or ask user? 
    # Let's try to find the first workspace in DB
    db = SessionLocal()
    from backend.models_db import Workspace
    ws = db.query(Workspace).first()
    db.close()
    
    if ws:
        verify_integrations(ws.id)
    else:
        print("No workspaces found in database. Cannot test.")
