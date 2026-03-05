
import os
import sys
import json
import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration
from backend.security import decrypt_text

def debug_handover():
    db = SessionLocal()
    try:
        # 1. Get Integration
        integration = db.query(Integration).filter(
            Integration.provider == "instagram",
            Integration.is_active == True
        ).first()
        
        if not integration:
            print("❌ No active Instagram integration found.")
            return

        # 2. Extract Token
        access_token_encrypted = integration.credentials
        if not access_token_encrypted:
             print("❌ No credentials found.")
             return
             
        try:
            decrypted = decrypt_text(access_token_encrypted)
            # Try to parse as JSON first (if it's a dict with access_token)
            try:
                creds = json.loads(decrypted)
                if isinstance(creds, dict) and "access_token" in creds:
                    access_token = creds["access_token"]
                else:
                    access_token = decrypted
            except json.JSONDecodeError:
                # Not JSON, assuming it's the raw token string
                access_token = decrypted
        except Exception as e:
             print(f"❌ Decryption failed: {e}")
             return

        if not access_token or access_token == "[Encrypted Data]":
             print("❌ Invalid decrypted token")
             return

        # 3. Get Page ID
        pages_resp = requests.get(f"https://graph.facebook.com/v21.0/me/accounts?access_token={access_token}")
        pages = pages_resp.json().get("data", [])
        if not pages:
            print("❌ No Page found.")
            return
            
        page = pages[0]
        page_id = page["id"]
        page_token = page["access_token"]
        print(f"✅ Page: {page['name']} (ID: {page_id})")

        # 4. Check Secondary Receivers (Handover Protocol)
        print("\n🔍 Checking Handover Protocol...")
        sec_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/secondary_receivers?fields=id,name&access_token={page_token}")
        print("Secondary Receivers:", json.dumps(sec_resp.json(), indent=2))
        
        # 5. Check Thread Owner of a Conversation (if exists)
        convs_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/conversations?platform=instagram&access_token={page_token}")
        convs = convs_resp.json().get("data", [])
        if convs:
            thread_id = convs[0]["id"]
            print(f"\n🔍 Inspecting Thread: {thread_id}")
            # Try to get thread owner? Not easily directly, but we can try to take control
            
            # 6. Attempt to Take Thread Control
            print("⚡ Attempting to Take Thread Control...")
            take_resp = requests.post(
                f"https://graph.facebook.com/v21.0/{page_id}/take_thread_control",
                params={
                    "access_token": page_token,
                    "recipient": {"id": convs[0]["id"]} # Wait, recipient should be user ID not thread ID?
                    # Actually for IG, it's usually the user PSID.
                    # Let's try to get participants
                }
            )
            # Hardcoded correct User ID from previous diagnostic
            # Verified correct IDs from diagnostic logs
            target_user_id = "4225246364388312"
            
            # We also need the access token. Let's get it from the DB integration we fixed.
            # Re-fetching integration and token here is redundant as it's already done above.
            # Using the already extracted page_token and target_user_id.

            print(f"🔑 Using Page Token: {page_token[:10]}...")
            
            # Note: The original code had calls to pass_thread_control and take_thread_control
            # which are not defined. Assuming the intent was to use the existing take_thread_control
            # logic with the new target_user_id.
            
            if target_user_id:
                print(f"   Target User ID: {target_user_id}")
                take_resp = requests.post(
                    f"https://graph.facebook.com/v21.0/{page_id}/take_thread_control",
                    params={
                        "access_token": page_token,
                        "recipient": json.dumps({"id": target_user_id})
                    }
                )
                print(f"   Take Control: {take_resp.status_code} - {take_resp.text}")
            else:
                print("   Could not find user participant.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_handover()
