import requests
import json

BASE_URL = "http://localhost:8000"

def simulate_call_webhook(from_num, to_num):
    # Simulate call.answered event
    payload = {
        "data": {
            "event_type": "call.answered",
            "payload": {
                "call_control_id": "test-call-id-123",
                "direction": "inbound",
                "from": from_num,
                "to": to_num,
                "connection_id": "test-conn-id"
            }
        }
    }
    
    print(f"--- Simulating Inbound Call Answered: {from_num} -> {to_num} ---")
    # Note: This will attempt to create a LiveKit room, so it might fail silently in logs but we want to see the resolution.
    response = requests.post(f"{BASE_URL}/api/telnyx/webhook", json=payload)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    return response

if __name__ == "__main__":
    # Test with the same assigned number
    simulate_call_webhook("+15551112222", "+18382061295")
    
    print("\nCheck backend/debug_webhook_telnyx.log for resolution trace.")
