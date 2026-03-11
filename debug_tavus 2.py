
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVUS_API_KEY")
if not api_key:
    # Try to find it in .env manually if load_dotenv fails or key is missing
    try:
        with open('.env') as f:
            for line in f:
                if line.startswith('TAVUS_API_KEY'):
                    api_key = line.split('=')[1].strip()
                    break
    except:
        pass

if not api_key:
    print("Error: TAVUS_API_KEY not found in env")
    exit(1)

url = "https://tavusapi.com/v2/replicas"
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

try:
    print(f"Fetching from {url}...")
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        # Print first 2 items to see structure
        if "data" in data:
            print(json.dumps(data["data"][:2], indent=2))
        else:
            print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
