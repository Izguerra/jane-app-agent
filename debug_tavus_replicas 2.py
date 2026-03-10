import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVUS_API_KEY")
if not api_key:
    print("Error: TAVUS_API_KEY not found")
    exit(1)

url = "https://tavusapi.com/v2/replicas"
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

print(f"Testing GET {url}")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response Type:", type(data))
        print("Root Keys:", data.keys() if isinstance(data, dict) else "List")
        if isinstance(data, dict) and "data" in data:
            print("Data Type:", type(data["data"]))
            if len(data["data"]) > 0:
                print("First Replica Keys:", data["data"][0].keys())
    else:
        print("Error Response:", response.text)
except Exception as e:
    print("Exception:", e)
