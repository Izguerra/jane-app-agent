import os
import jwt
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
WORKSPACE_ID = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
AUTH_SECRET = os.getenv("AUTH_SECRET") or "SECRET_KEY_DEV" # Fallback if env missing

def generate_token():
    payload = {
        "workspace_id": WORKSPACE_ID,
        "role": "worker_instance",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm="HS256")

def test_api():
    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "status": "pending",
        "worker_type": "openclaw",
        "workspace_id": WORKSPACE_ID
    }
    
    print(f"Testing API: {BASE_URL}/workers/tasks")
    print(f"Params: {params}")
    
    try:
        response = requests.get(f"{BASE_URL}/workers/tasks", headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
