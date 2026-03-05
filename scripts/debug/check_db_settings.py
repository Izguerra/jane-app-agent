
import os
import sys
import json
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration

def check_settings():
    db = SessionLocal()
    try:
        print("🔍 Checking Stored Integration Settings...")
        integration = db.query(Integration).filter(
            Integration.provider == "instagram",
            Integration.is_active == True
        ).first()
        
        if not integration:
            print("❌ No active Instagram integration found.")
            return

        print(f"✅ Found Integration (ID: {integration.id})")
        if integration.settings:
            settings = json.loads(integration.settings)
            stored_id = settings.get("instagram_account_id")
            print(f"   Stored 'instagram_account_id': {stored_id}")
            print(f"   Full Settings: {json.dumps(settings, indent=2)}")
            
            # Known Webhook ID from logs
            webhook_id = "17841473513407245" 
            print(f"\n   Expected Webhook ID:       {webhook_id}")
            
            if str(stored_id) == webhook_id:
                print("✅ MATCH! Settings are correct.")
            else:
                print("❌ MISMATCH! The stored ID does not match the Webhook ID.")
                print("   (User likely connected with the Page ID or a different ID)")
        else:
            print("❌ Settings field is empty.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_settings()
