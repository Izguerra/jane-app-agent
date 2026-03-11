import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration
from backend.security import decrypt_text

def check_subs():
    db = SessionLocal()
    try:
        # 1. Get Integration
        integration = db.query(Integration).filter(
            Integration.provider == "instagram",
            Integration.is_active == True
        ).first()

        if not integration:
            print("❌ No active integration")
            return

        settings = json.loads(integration.settings)
        access_token = settings.get("access_token")
        
        # Try decrypt if not in settings
        if not access_token and integration.credentials:
             try:
                creds = json.loads(decrypt_text(integration.credentials))
                access_token = creds.get("access_token")
             except:
                pass
        
        print(f"Token: {access_token[:10]}...")

        # 2. Get Page ID
        me_resp = requests.get(f"https://graph.facebook.com/v21.0/me/accounts?access_token={access_token}")
        data = me_resp.json().get("data", [])
        if not data:
             print("❌ No Page found")
             return
             
        page = data[0]
        page_id = page["id"]
        page_token = page["access_token"]
        print(f"Page: {page['name']} ({page_id})")

        # 3. Request Subscribed Apps
        print("🔍 Checking Subscribed Fields...")
        sub_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/subscribed_apps?access_token={page_token}")
        print(json.dumps(sub_resp.json(), indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_subs()
