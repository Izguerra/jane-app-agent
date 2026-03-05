
import jwt
import time
import os
import sys

# Hardcoded for verification
SECRET = "7f3b2a1c9d8e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9"
USER_ID = "750e9496-2843-4800-b2b1-e2b0a2d6940f"
TEAM_ID = "org_000V7dMzThAVrPNF3XBlRXq4MO"

def generate_token():
    payload = {
        "user": {
            "id": USER_ID,
            "teamId": TEAM_ID,
            "role": "owner",
            "name": "Randy Esguerra"
        },
        "email": "resguerra75@gmail.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600 * 24 # 24 hours
    }
    
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    print(token)

if __name__ == "__main__":
    generate_token()
