import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TAVUS_API_KEY")
url = "https://tavusapi.com/v2"

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

def check_persona():
    payload = {
        "persona_name": "test_persona",
        "pipeline_mode": "echo",
        "layers": {
            "transport": {"transport_type": "livekit"},
        },
    }
    r = requests.post(f"{url}/personas", json=payload, headers=headers)
    print("CREATE PERSONA:", r.status_code, r.text)
    if r.status_code == 200:
        return r.json().get("persona_id")
    return None

def check_convo(persona_id):
    payload = {
        "replica_id": "r6ae5b6efc9d",
        "persona_id": persona_id,
        "conversation_name": "Test Conv",
    }
    r = requests.post(f"{url}/conversations", json=payload, headers=headers)
    print("CREATE CONVO:", r.status_code, r.text)

if __name__ == "__main__":
    pid = check_persona()
    if pid:
        check_convo(pid)
