"""
Test Gmail Connection
Directly invokes GmailIntegration to test connectivity and credentials.
"""
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.services.gmail_service import GmailService
import traceback

WORKSPACE_ID = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"

def test_gmail():
    db = SessionLocal()
    try:
        print(f"Testing Gmail connection for workspace: {WORKSPACE_ID}")
        
        service = GmailService(db)
        integration = service._get_integration(WORKSPACE_ID)
        
        if not integration:
            print("ERROR: Integration not found via service query!")
            return
            
        print(f"Found Integration ID: {integration.id}")
        
        # Test 1: Service Build
        print("Attempting to build Google Service...")
        try:
            g_service = service._get_service(integration)
            print("Service built successfully.")
        except Exception as e:
            print(f"ERROR Building Service: {e}")
            traceback.print_exc()
            return

        # Test 2: List Emails
        print("Attempting to list emails...")
        try:
            emails = service.list_emails(WORKSPACE_ID, limit=5)
            print(f"Success! Found {len(emails)} emails.")
            for e in emails:
                print(f"- [{e['date']}] {e['from']}: {e['subject']}")
        except Exception as e:
            print(f"ERROR Listing Emails: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"General Error: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_gmail()
