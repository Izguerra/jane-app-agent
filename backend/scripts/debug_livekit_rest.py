import os
import time
import httpx
from livekit import api
from dotenv import load_dotenv

async def debug_livekit_connection():
    load_dotenv()
    
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    # Convert wss:// to https:// for REST API
    http_url = url.replace("wss://", "https://").replace("ws://", "http://")
    
    print(f"DEBUG: Using URL: {http_url}")
    print(f"DEBUG: Using Key: {key}")
    
    # Use AccessToken to verify auth
    token = api.AccessToken(key, secret) \
        .with_grants(api.VideoGrants(room_list=True, room_admin=True)) \
        .to_jwt()
    
    print(f"DEBUG: Generated Token (first 20 chars): {token[:20]}...")
    
    async with httpx.AsyncClient() as client:
        # LiveKit uses Twirp (Protobuf over HTTP)
        # We can send an empty JSON for ListRooms
        try:
            response = await client.post(
                f"{http_url}/twirp/livekit.RoomService/ListRooms",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            
            print(f"DEBUG: Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                rooms = data.get("rooms", [])
                print(f"DEBUG: Found {len(rooms)} rooms via REST API.")
                for room in rooms:
                    print(f" - {room.get('name')} (Participants: {room.get('num_participants')})")
                    # Try to delete it
                    del_res = await client.post(
                        f"{http_url}/twirp/livekit.RoomService/DeleteRoom",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={"room": room.get("name")}
                    )
                    print(f"   -> Delete result: {del_res.status_code}")
            else:
                print(f"DEBUG: Error Response: {response.text}")
        except Exception as e:
            print(f"DEBUG: Request failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_livekit_connection())
