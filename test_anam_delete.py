import httpx
import asyncio
import os
import jwt
from datetime import datetime, timedelta

async def test_anam_delete():
    # 1. Create a token exactly as NextJS AuthUser does
    secret = os.getenv("AUTH_SECRET", "super-secret-key-123")
    
    payload = {
        "user": {
            "id": "dev_user",
            "teamId": "org_000V7dMzThAVrPNF3XBlRXq4MO",
            "role": "admin",
            "name": "Developer Admin"
        },
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    print(f"Token created: {token[:50]}...")
    
    headers = {"Authorization": "Bearer DEVELOPER_BYPASS"}
    async with httpx.AsyncClient() as client:
        # GET integrations first
        get_resp = await client.get("http://127.0.0.1:8000/agent/integrations", headers=headers)
        print(f"GET /integrations: {get_resp.status_code}")
        
        if get_resp.status_code == 200:
            print(get_resp.json())
            
        # Try to DELETE anam
        print("Sending DELETE /agent/integrations/anam")
        del_resp = await client.delete("http://127.0.0.1:8000/agent/integrations/anam", headers=headers)
        
        print(f"DELETE status: {del_resp.status_code}")
        try:
            print(f"DELETE body: {del_resp.json()}")
        except:
             print(f"DELETE text: {del_resp.text}")

if __name__ == "__main__":
    asyncio.run(test_anam_delete())
