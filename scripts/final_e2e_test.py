
import asyncio
import httpx
import sys
import os
import jwt

# Questions to verify
QUESTIONS = [
    "What is the weather in Vancouver, BC?",
    "What is the status of flight AC196?",
    "What is the best sushi restaurant in Milton, ON?"
]

# Use 127.0.0.1 to avoid localhost resolution issues
BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = "7f3b2a1c9d8e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9"
WORKSPACE_ID = "wrk_000V8CE9odAz9V9NXuH7dYFbOz"
TEAM_ID = "org_000V8CE9lZkyaPTVHy1EHe73dg"

async def test_ping():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/ping")
            print(f"Ping result: {resp.status_code} {resp.text}")
            return resp.status_code == 200
        except Exception as e:
            print(f"Ping failed: {e}")
            return False

async def test_question(question, token):
    print(f"\nTESTING: {question}")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": question,
        "history": [],
        "agent_id": None # Use default agent
    }
    
    full_response = ""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # We use a single try/except block for the stream to avoid closure issues
            async with client.stream("POST", f"{BASE_URL}/chat", json=payload, headers=headers) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    print(f"❌ HTTP Error {response.status_code}")
                    print(f"Error Body: {body.decode()}")
                    return False
                
                async for chunk in response.aiter_text():
                    if chunk:
                        full_response += chunk
                        # Print indicators
                        if "working on" in chunk.lower() or "wait" in chunk.lower() or "one second" in chunk.lower():
                            print(".", end="", flush=True)
                        else:
                            print(f"#", end="", flush=True)
        
        print("\n")
        if len(full_response.strip()) < 50:
            print(f"❌ FAIL: Response too short or empty: '{full_response}'")
            return False
            
        print(f"✅ SUCCESS: Full response length: {len(full_response)}")
        print(f"Preview: {full_response[:300]}...")
        return True
    except Exception as e:
        print(f"\n❌ FAIL: Exception during request: {e}")
        return False

async def main():
    if not await test_ping():
        print("❌ Backend is not reachable at 127.0.0.1:8000. Ensure it is running.")
        sys.exit(1)
        
    # Create a realistic token
    payload = {
        "user": {
            "id": "test_user_e2e",
            "teamId": TEAM_ID,
            "workspaceId": WORKSPACE_ID,
            "role": "owner",
            "email": "tester@example.com",
            "name": "E2E Tester"
        }
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    all_passed = True
    for q in QUESTIONS:
        success = await test_question(q, token)
        if not success:
            all_passed = False
            
    print("\n--- FINAL E2E SUMMARY ---")
    if all_passed:
        print("🚀 100% PASS - ALL QUESTIONS ANSWERED SUCCESSFULLY")
    else:
        print("❌ FAIL - ONE OR MORE QUESTIONS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
