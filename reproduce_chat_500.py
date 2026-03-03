import requests
import json

def test_chat():
    url = "http://localhost:8000/chat"
    # Note: This requires a valid user session or token if protected
    # Let's assume for local testing we can bypass or use a test token
    
    payload = {
        "message": "hi",
        "history": [],
        "agent_id": None
    }
    
    # We might need headers if there's auth
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
