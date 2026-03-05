
from backend.services.tavus_service import TavusService
import json
import os
from dotenv import load_dotenv

load_dotenv()

def inspect():
    ts = TavusService()
    print("Fetching replicas...")
    replicas = ts.list_replicas()
    if replicas:
        print(f"Found {len(replicas)} replicas.")
        print("Sample Replica:")
        print(json.dumps(replicas[0], indent=2))
    else:
        print("No replicas found or error.")

if __name__ == "__main__":
    inspect()
