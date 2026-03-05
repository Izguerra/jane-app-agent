
import requests
import json
import os

def test_token_request():
    url = "http://localhost:8000/voice/token"
    
    payload = {
        "workspace_id": "org_000V7dMzThAVrPNF3XBlRXq4MO",
        "participant_name": "Test User",
        "mode": "voice"
    }
    
    headers = {
        "Authorization": "Bearer DEVELOPER_BYPASS",
        "Content-Type": "application/json"
    }
    
    print(f"Requesting token from {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Token received: {data.get('token')[:50]}...")
            print(f"LiveKit URL: {data.get('url')}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_token_request()
