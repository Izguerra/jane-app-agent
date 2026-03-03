
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")

if not TAVUS_API_KEY:
    print("Error: TAVUS_API_KEY not found in environment variables.")
    exit(1)

def test_tavus_api():
    print("Testing Tavus API Connection...")
    
    # Check Replicas (Avatars)
    url = "https://tavusapi.com/v2/replicas"
    headers = {
        "x-api-key": TAVUS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            replicas = response.json().get("data", [])
            print(f"✅ Success! Connected to Tavus API.")
            print(f"Found {len(replicas)} replicas.")
            if replicas:
                print(f"First Replica ID: {replicas[0].get('replica_id')}")
                print(f"First Replica Name: {replicas[0].get('replica_name')}")
            else:
                print("No replicas found (account has access but no avatars created).")
        else:
            print(f"❌ Failed to connect. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_tavus_api()
