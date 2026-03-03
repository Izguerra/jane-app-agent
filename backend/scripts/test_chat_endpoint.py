
import requests
import json
import sys
import os

# Ensure backend URL is correct
BACKEND_URL = "http://127.0.0.1:8000"

def test_chat():
    print(f"Testing Chat Endpoint at {BACKEND_URL}...")
    
    # 1. Health check first
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Health Check: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return

    # 2. Chat Request (mimicking Next.js payload)
    # Usually Next.js sends { messages: [...], workspace_id: ... } or similar.
    # We'll try a simple message.
    
    payload = {
        "messages": [
            {"role": "user", "content": "What is the weather in Toronto?"}
        ],
        "workspace_id": "test_workspace", # specific ID might be needed
        "agent_id": "test_agent"
    }

    try:
        # Check endpoint path: /chat or /api/chat?
        # Based on analysis, likely /chat
        url = f"{BACKEND_URL}/chat" 
        print(f"Sending POST to {url} with payload: {payload}")
        
        resp = requests.post(url, json=payload, timeout=30)
        
        if resp.status_code == 200:
            print("✅ Chat Request Successful!")
            print(f"Response: {resp.text[:200]}...") # Truncate
        else:
            print(f"❌ Chat Request Failed: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Chat Exception: {e}")

if __name__ == "__main__":
    test_chat()
