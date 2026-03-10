import os
import sys
from dotenv import load_dotenv

# Add backend directory to path to use backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import telnyx
from backend.services.integration_service import IntegrationService
from backend.models_db import PhoneNumber
from backend.database import SessionLocal

load_dotenv()

def verify_and_update_telnyx_webhook():
    print("Fetching active ngrok URL...")
    import requests
    try:
        ngrok_resp = requests.get("http://localhost:4040/api/tunnels").json()
        public_url = ngrok_resp['tunnels'][0]['public_url']
        webhook_url = f"{public_url}/api/telnyx/webhook"
        print(f"Target Webhook URL: {webhook_url}")
    except Exception as e:
        print(f"Failed to get ngrok URL: {e}")
        return

    # Find Telnyx API Key
    db = SessionLocal()
    telnyx_number = "+18382061295"
    phone_record = db.query(PhoneNumber).filter(PhoneNumber.phone_number == telnyx_number).first()
    workspace_id = phone_record.workspace_id if phone_record else None
    
    telnyx_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="telnyx", env_fallback="TELNYX_API_KEY")
    connection_id = "2909190246035883291" # Hardcoded from old .env
    
    if not telnyx_key or not connection_id:
        print("Missing Telnyx API Key or Connection ID")
        return

    telnyx.api_key = telnyx_key

    try:
        print(f"Fetching connection details for ID: {connection_id}...")
        import requests
        headers = {
            "Authorization": f"Bearer {telnyx_key}",
            "Content-Type": "application/json"
        }
        
        # Check Call Control Application
        app_type = None
        current_url = None
        
        cc_resp = requests.get(f"https://api.telnyx.com/v2/call_control_applications/{connection_id}", headers=headers)
        if cc_resp.status_code == 200:
            app_type = "call_control"
            current_url = cc_resp.json()["data"]["webhook_event_url"]
            print(f"Found Call Control App. Current Webhook URL: {current_url}")
        else:
            # Check TeXML Application
            texml_resp = requests.get(f"https://api.telnyx.com/v2/texml_applications/{connection_id}", headers=headers)
            if texml_resp.status_code == 200:
                app_type = "texml"
                # TeXML apps have voice_url
                current_url = texml_resp.json()["data"]["voice_url"]
                print(f"Found TeXML App. Current Voice URL: {current_url}")
            else:
                print(f"Could not find application with ID {connection_id} in CC or TeXML apps.")
                print("CC Errors:", cc_resp.text)
                print("TeXML Errors:", texml_resp.text)
                return

        expected_url = f"{public_url}/api/telnyx/webhook" if app_type == "call_control" else f"{public_url}/api/telnyx/texml/inbound"
        
        if current_url != expected_url:
            print("Updating URL...")
            if app_type == "call_control":
                payload = {"webhook_event_url": expected_url}
                patch_resp = requests.patch(f"https://api.telnyx.com/v2/call_control_applications/{connection_id}", headers=headers, json=payload)
            else:
                # TeXML application
                payload = {
                    "voice_url": expected_url,
                    "voice_fallback_url": "",
                    "voice_method": "POST"
                }
                patch_resp = requests.patch(f"https://api.telnyx.com/v2/texml_applications/{connection_id}", headers=headers, json=payload)
                
            if patch_resp.status_code == 200:
                print(f"Successfully updated Telnyx {app_type} Application to {expected_url}")
            else:
                print(f"Failed to update! Status: {patch_resp.status_code}, Response: {patch_resp.text}")
        else:
            print(f"URL is already correct ({expected_url}).")

    except Exception as e:
        print(f"Error accessing Telnyx API: {e}")

if __name__ == "__main__":
    verify_and_update_telnyx_webhook()
