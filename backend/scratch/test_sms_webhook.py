import requests
import json
import time

BASE_URL = "http://localhost:8000"

def simulate_sms_webhook(from_num, to_num, text):
    payload = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "direction": "inbound",
                "from": {
                    "phone_number": from_num
                },
                "to": [
                    {
                        "phone_number": to_num
                    }
                ],
                "text": text,
                "type": "SMS"
            }
        }
    }
    
    print(f"--- Simulating Inbound SMS: {from_num} -> {to_num} ---")
    response = requests.post(f"{BASE_URL}/api/telnyx/sms/webhook", json=payload)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    return response

def check_resolved_agent(comm_id):
    # This requires querying the DB or checking logs
    # For simplicity, we'll check the backend log for our new log messages
    pass

if __name__ == "__main__":
    # Test with the existing unassigned number
    # This should fallback to an active agent (Supa Agent in this workspace)
    simulate_sms_webhook("+15556667777", "+18382061295", "Hello from verification script!")
    
    print("\nCheck backend.log or debug_webhook_telnyx.log for resolution trace.")
