
from backend.database import SessionLocal
from backend.models_db import PlatformIntegration
import uuid

def seed_missing():
    db = SessionLocal()
    try:
        # Check for Gmail
        gmail = db.query(PlatformIntegration).filter_by(provider="gmail_mailbox").first()
        if not gmail:
            print("Adding Gmail...")
            db.add(PlatformIntegration(
                id=str(uuid.uuid4()),
                provider="gmail_mailbox",
                display_name="Gmail",
                description="Read and send emails via Gmail",
                is_enabled=True
            ))
        else:
            print("Gmail exists.")

        # Check for Outlook
        outlook = db.query(PlatformIntegration).filter_by(provider="outlook_mailbox").first()
        if not outlook:
            print("Adding Outlook...")
            db.add(PlatformIntegration(
                id=str(uuid.uuid4()),
                provider="outlook_mailbox",
                display_name="Outlook Mail",
                description="Read and send emails via Outlook",
                is_enabled=True
            ))
        else:
            print("Outlook exists.")

        # Check for iCloud
        icloud = db.query(PlatformIntegration).filter_by(provider="icloud_mailbox").first()
        if not iCloud:
            print("Adding iCloud...")
            db.add(PlatformIntegration(
                id=str(uuid.uuid4()),
                provider="icloud_mailbox",
                display_name="iCloud Mail",
                description="Read and send emails via iCloud",
                is_enabled=True
            ))
        else:
            print("iCloud exists.")

        db.commit()
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        # Identify name error if any
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_missing()
