import requests
import os
import json

TELNYX_KEY = os.getenv("TELNYX_API_KEY", "")
CALL_ID = "v3:4PzgzxKfFLunx0k_RgMXyDcSyX1WS5c7XW79X17cPP2wQ_gx_Ske3g"  # An expired call id, might get 404 or 400 instead of 422 if payload is valid

def test_payload(payload_name, payload):
    url = f"https://api.telnyx.com/v2/calls/{CALL_ID}/actions/transfer"
    headers = {
        "Authorization": f"Bearer {TELNYX_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=payload, headers=headers)
    print(f"{payload_name}: {resp.status_code}")
    print(resp.text)
    print("-" * 40)

p1 = {
    "to": "sip:test@147.182.149.234",
    "sip_headers": [
        {"name": "X-LiveKit-Room", "value": "inbound-test"}
    ]
}

p2 = {
    "to": "sip:test@147.182.149.234",
    "custom_headers": [
        {"name": "X-LiveKit-Room", "value": "inbound-test"}
    ]
}

test_payload("Array of Objects (sip_headers)", p1)
test_payload("Array of Objects (custom_headers)", p2)

