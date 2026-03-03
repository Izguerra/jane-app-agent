import os
import httpx
import asyncio
from dotenv import load_dotenv

import jwt
from datetime import datetime, timedelta

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SECRET_KEY = os.getenv("AUTH_SECRET")

def generate_test_token():
    payload = {
        "user": {
            "id": "usr_test_e2e",
            "teamId": "org_000V7dMzThAVrPNF3XBlRXq4MO", # The org ID we saw in logs
            "role": "supaagent_admin"
        },
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

AUTH_TOKEN = generate_test_token()

async def test_chat_session():
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    agent_id = "agnt_000VA6fCM7ooHx7VALTwm40ed8"
    
    # We'll use the /agents/{agent_id}/chat endpoint
    # Note: We need a valid session. We can simulate one by providing a user_identifier.
    
    url = f"{BACKEND_URL}/chat"
    payload = {
        "agent_id": agent_id,
        "message": "Can you go to https://example.com and tell me the page title?",
        "history": []
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"Sending chat message to agent {agent_id}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code == 200:
                print("Chat Response:")
                print(response.json())
            else:
                print(f"Chat failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_session())
