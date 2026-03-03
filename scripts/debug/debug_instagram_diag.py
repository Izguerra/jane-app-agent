
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

def debug_diag():
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
            try:
                creds = json.loads(decrypted)
                if isinstance(creds, dict) and "access_token" in creds:
                    access_token = creds["access_token"]
                else:
                    access_token = decrypted
            except json.JSONDecodeError:
                access_token = decrypted
        except Exception as e:
             print(f"❌ Decryption failed: {e}")
             return

        # 3. Get Page ID
        print(f"Token: {access_token[:15]}...")
        # 2. Inspect Token Identity
        GRAPH_URL = "https://graph.facebook.com/v21.0"
        identity = requests.get(f"{GRAPH_URL}/me?access_token={access_token}&fields=id,name")
        print(f"Token Identity: {identity.json()}")

        # 3. List Pages
        print("3. List Pages (checking /me/accounts)...")
        
        # Check permissions first
        GRAPH_URL = "https://graph.facebook.com/v21.0"
        try:
            perm_url = f"{GRAPH_URL}/me/permissions?access_token={access_token}"
            perm_res = requests.get(perm_url)
            print(f"Permissions: {perm_res.json()}")
        except Exception as e:
            print(f"Perm Check Failed: {e}")

        accounts_url = f"{GRAPH_URL}/me/accounts?access_token={access_token}"
        resp = requests.get(accounts_url)
        try:
            data = resp.json()
            print(f"Pages Raw: {json.dumps(data)}")
            pages = data.get("data", [])
        except Exception as e:
            print(f"Error parsing accounts response: {e}")
            pages = []

        if not pages:
            # Maybe the token IS a page token? Try /me
            print("❌ No Page found in /me/accounts. Checking /me (if it's a Page Token)...")
            me_resp = requests.get(f"https://graph.facebook.com/v21.0/me?fields=id,name,access_token&access_token={access_token}")
            me_data = me_resp.json()
            if "id" in me_data and "access_token" not in me_data: 
                # If checking /me with page token, access_token field might not be returned? 
                # Actually, /me for a page returns page info.
                print(f"   /me Info: {me_data}")
                page_id = me_data["id"]
                page_Name = me_data.get("name")
                # If we used a page token, we don't need to extract one.
                print(f"✅ It seems effective token is for Page: {page_Name} (ID: {page_id})")
                # We can proceed using the existing access_token
            else:
                return
        else:    
            page = pages[0]
            page_id = page["id"]
            page_token = page["access_token"] # Extract Page Token
            print(f"✅ Page: {page['name']} (ID: {page_id})")

        # 3.5 Check Subscriptions
        print("🔍 Checking Active Subscriptions...")
        sub_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/subscribed_apps?access_token={page_token}")
        print(f"   Subs: {json.dumps(sub_resp.json(), indent=2)}")

        # 4. List Conversations (Using Page Token)
        print("\n🔍 Fetching Conversations...")
        # Use page_token instead of access_token (User Token)
        conv_resp = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/conversations?platform=instagram&access_token={page_token}")
        convs = conv_resp.json().get("data", [])
        print(f"✅ Found {len(convs)} conversations.")
        
        target_conv_id = None
        
        for i, conv in enumerate(convs):
            print(f"\n   [{i}] Conversation ID: {conv['id']} (Updated: {conv.get('updated_time')})")
            
            # Get Messages in Thread
            msg_resp = requests.get(f"https://graph.facebook.com/v21.0/{conv['id']}?fields=messages{{message,from,to,created_time}}&access_token={page_token}")
            msgs = msg_resp.json().get("messages", {}).get("data", [])
            
            if msgs:
                last_msg = msgs[0]
                print(f"       Last Msg: '{last_msg.get('message')}' from {last_msg.get('from', {}).get('name')}")
                # We want to reply to this checks validity
                target_conv_id = conv['id']
                # Try to get the user's IGSID
                # 'from' might be the user or the page.
                sender_id = last_msg.get('from', {}).get('id')
                if sender_id != page_id:
                     print(f"       User ID: {sender_id} (Target for manual reply)")
                     
                     # 5. ATTEMPT REPLY
                     print(f"       ⚡ Attempting Manual API Reply to User {sender_id}...")
                     reply_resp = requests.post(
                         f"https://graph.facebook.com/v21.0/me/messages?access_token={page_token}",
                         json={
                             "recipient": {"id": sender_id},
                             "message": {"text": "✅ DIAGNOSTIC TEST: The Agent CAN reply via API. If you see this, the Outbound Path is 100% working."}
                         },
                         headers={"Content-Type": "application/json"}
                     )
                     print(f"       Reply Result: {reply_resp.status_code} - {reply_resp.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_diag()
