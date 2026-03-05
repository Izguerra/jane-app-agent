import os
import json
import jwt
from dotenv import load_dotenv
import time
import urllib.request
import urllib.error

load_dotenv('.env')

SECRET_KEY = os.getenv("AUTH_SECRET")
ALGORITHM = "HS256"

# Create a test token
payload = {
    "user": {
         "id": "usr_test_manual",
         "teamId": "tm_test_manual",
         "role": "owner"
    },
    "email": "manual@test.com",
    "exp": time.time() + 3600
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"Generated Token: {token[:10]}...")

def test_url(name, headers):
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/customers/", headers=headers)
        with urllib.request.urlopen(req) as resp:
            print(f"{name} Result: {resp.status}")
            print(resp.read().decode('utf-8')[:200])
    except urllib.error.HTTPError as e:
        print(f"{name} Request Failed: {e.code} {e.reason}")
        print(e.read().decode('utf-8')[:200])
    except Exception as e:
        print(f"{name} Error: {e}")

# Test 1: Header Auth
test_url("Header Auth (Bearer)", {"Authorization": f"Bearer {token}"})

# Test 2: Cookie Auth
test_url("Cookie Auth", {"Cookie": f"session={token}"})
