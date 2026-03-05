
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

from backend.database import SessionLocal, get_db
from backend.models_db import Integration
from backend.security import decrypt_text

def debug_subscription():
    db = SessionLocal()
    try:
        # 1. Get Integration
        integration = db.query(Integration).filter(
            Integration.provider == "instagram",
            Integration.is_active == True
        ).first()
        
        if not integration:
            print("❌ No active Instagram integration found in DB.")
            return

        print(f"✅ Found Integration ID: {integration.id}")
        print(f"Settings raw: '{integration.settings}'")
        print(f"Credentials raw: '{integration.credentials}'")
        
        # 2. Get Credentials
        if integration.settings:
            try:
                settings = json.loads(integration.settings)
            except json.JSONDecodeError:
                print("❌ Settings JSON Decode Error")
                settings = {}
        else:
            settings = {}
        access_token_encrypted = settings.get("access_token") # Or credentials?
        
        # In routers/integrations.py, it seems access_token is in settings for instagram?
        # Let's check credentials dict if settings is empty/missing
        if not access_token_encrypted:
             access_token_encrypted = integration.credentials
             
        if not access_token_encrypted:
            print("❌ No access_token found in settings or credentials.")
            return

        # 3. Decrypt
        try:
            # Check if it looks like a JSON dict from credentials field first
            decrypted_creds = decrypt_text(access_token_encrypted)
            print(f"Decrypted creds raw: {decrypted_creds[:50]}...")
            
            try:
                creds_json = json.loads(decrypted_creds)
                if isinstance(creds_json, dict) and "access_token" in creds_json:
                    access_token = creds_json["access_token"]
                else:
                    access_token = decrypted_creds
            except:
                access_token = decrypted_creds

            if not access_token or access_token == "[Encrypted Data]":
                 print("❌ Failed to decrypt token.")
                 return
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return

        print(f"✅ Token decrypted (starts with): {access_token[:10]}...")
        
        # 4. Debug Token (Check Scopes)
        print("\n🔍 Checking Token Scopes...")
        debug_resp = requests.get(
            "https://graph.facebook.com/v21.0/debug_token",
            params={
                "input_token": access_token,
                "access_token": access_token # Using itself to debug itself (works if app token not available)
            }
        )
        if debug_resp.status_code == 200:
            data = debug_resp.json().get("data", {})
            print(f"✅ Token Valid: {data.get('is_valid')}")
            print(f"✅ Scopes: {', '.join(data.get('scopes', []))}")
            # Check for key permissions
            required = ["instagram_basic", "instagram_manage_messages", "pages_show_list", "pages_messaging"]
            missing = [s for s in required if s not in data.get("scopes", [])]
            if missing:
                print(f"⚠️ MISSING PERMISSIONS: {missing}")
        else:
            print(f"⚠️ Could not debug token: {debug_resp.text}")

        # 5. Get User Info (Check if token is valid)
        me_resp = requests.get(f"https://graph.facebook.com/v21.0/me?access_token={access_token}")
        me_data = me_resp.json()
        print(f"✅ Token belongs to: {me_data.get('name')} (ID: {me_data.get('id')})")
        
        # 6. Check Pages
        pages_resp = requests.get(f"https://graph.facebook.com/v21.0/me/accounts?access_token={access_token}")
        pages_data = pages_resp.json()
        
        if not pages_data.get("data"):
            print("❌ No Pages found for this user.")
            return
            
        page = pages_data["data"][0] # Assuming first page
        page_id = page["id"]
        page_token = page["access_token"]
        page_name = page["name"]
        
        print(f"✅ Found Page: {page_name} (ID: {page_id})")
        
        # 7. Force Subscribe (Blindly, getting list might fail)
        print("⚡ Force-Subscribing App to Page...")
        sub_post = requests.post(
            f"https://graph.facebook.com/v21.0/{page_id}/subscribed_apps",
            params={
                "access_token": page_token,
                "subscribed_fields": "messages,messaging_postbacks,message_reactions" # Extended fields
            }
        )
        print(f"Subscribe Result: {sub_post.status_code} - {sub_post.text}")
        if sub_post.status_code == 200 and sub_post.json().get("success"):
            print("✅ SUCCESSFULLY SUBSCRIBED APP TO PAGE (Extended Fields)!")
        else:
             print("❌ FAILED TO SUBSCRIBE.")

        # 8. Check Conversations (Test Permission)
        print("\n🔍 Testing 'read' permission by fetching conversations...")
        conv_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/conversations?platform=instagram&access_token={page_token}")
        if conv_resp.status_code == 200:
            convs = conv_resp.json()
            print(f"✅ Found {len(convs.get('data', []))} conversations.")
            print(json.dumps(convs, indent=2))
        else:
             print(f"❌ Failed to fetch conversations: {conv_resp.status_code} - {conv_resp.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_subscription()
