import os
import requests
from backend.database import SessionLocal
from backend.models_db import PhoneNumber
from backend.services.integration_service import IntegrationService

CALL_ID = "v3:4PzgzxKfFLunx0k_RgMXyDcSyX1WS5c7XW79X17cPP2wQ_gx_Ske3g"

db = SessionLocal()
phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == '+18382061295').first()
workspace_id = phone.workspace_id
telnyx_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="telnyx", env_fallback="TELNYX_API_KEY")
print("KEY LOADED:", bool(telnyx_key))
db.close()

def test_payload(name, payload):
    url = f"https://api.telnyx.com/v2/calls/{CALL_ID}/actions/transfer"
    headers = {
        "Authorization": f"Bearer {telnyx_key}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=payload, headers=headers)
    print(f"--- {name} ---")
    print(f"Status: {resp.status_code}")
    print(resp.text)

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

test_payload("sip_headers X-LiveKit-Room", p1)
test_payload("custom_headers X-LiveKit-Room", p2)
