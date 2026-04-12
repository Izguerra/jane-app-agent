import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Use NGROK_URL if testing locally, or DO_IP if testing remote
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("TEST_USER_API_KEY") # You might need a valid token

def test_provisioning_flow():
    print(f"🚀 Starting Provisioning Test against {BASE_URL}...")
    
    # Need a valid workspace_id and agent_id for SupaAgent
    # From previous logs: workspace_id='WS_001', agent_id='supaagent-voice-agent-v2' (or similar ID)
    # Let's find the SupaAgent agent ID
    
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" 
    agent_id = "agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ" # This name is often used as the ID/name mapping
    
    payload = {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "provider": "telnyx",
        "country_code": "US",
        "area_code": "838",
        "friendly_name": "Provisioning Test Number"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        print(f"📡 Sending purchase request for area code 838...")
        response = requests.post(f"{BASE_URL}/phone-numbers/purchase", json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"✅ SUCCESS! Provisioned number: {data['phone_number']}")
            print(f"🔗 Linked to Agent: {data.get('agent_name', 'Unknown')}")
            print(f"📝 Number ID: {data['id']}")
            
            # Now verify reassignment logic
            print(f"🔄 Testing Unassign (setting agent_id to None)...")
            assign_payload = {"agent_id": None}
            patch_res = requests.patch(f"{BASE_URL}/phone-numbers/{data['id']}/assign", json=assign_payload, headers=headers)
            if patch_res.status_code == 200:
                print(f"✅ Successfully unassigned agent.")
            else:
                print(f"❌ Failed to unassign: {patch_res.text}")

        else:
            print(f"❌ FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"💥 Error during test: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️  Warning: TEST_USER_API_KEY not found in .env. Test might fail 401.")
    test_provisioning_flow()
