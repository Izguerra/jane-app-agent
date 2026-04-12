import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def simulate_sms_webhook_duplicate(from_num, to_num, text, msg_id):
    payload = {
        "data": {
            "id": msg_id,
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
    
    print(f"--- Simulating Inbound SMS (ID: {msg_id}) ---")
    response = requests.post(f"{BASE_URL}/api/telnyx/sms/webhook", json=payload)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    return response

if __name__ == "__main__":
    msg_id = str(uuid.uuid4())
    
    # 1. Send first message
    print("Sending first message...")
    simulate_sms_webhook_duplicate("+15556667777", "+18382061295", "Hello! This is a test for deduplication.", msg_id)
    
    # 2. Immediately send the same message again (simulating Telnyx retry)
    print("\nSending duplicate message (Telnyx retry simulation)...")
    simulate_sms_webhook_duplicate("+15556667777", "+18382061295", "Hello! This is a test for deduplication.", msg_id)
    
    print("\nCheck backend.log for 'Duplicate Telnyx SMS ignored' and verify ONLY ONE AI generation occurs.")
