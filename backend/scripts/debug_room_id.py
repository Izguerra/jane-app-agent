import os
import asyncio
import httpx
from livekit import api
from dotenv import load_dotenv

async def debug_specific_room_id():
    load_dotenv()
    url = os.getenv("LIVEKIT_URL").replace("wss://", "https://")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    # Room ID from the user screenshot
    room_id = "RM_AuYLzd4PCUfE"
    
    token = api.AccessToken(key, secret) \
        .with_grants(api.VideoGrants(room_admin=True)) \
        .to_jwt()
    
    async with httpx.AsyncClient() as client:
        # Check if we can get info for this room ID
        # Note: LiveKit RoomService usually takes Room Name, not Room ID
        # But we can try to list participants if we have the name
        room_name = "agent-session-agnt_000-avatar" 
        
        print(f"DEBUG: Checking room name {room_name}...")
        response = await client.post(
            f"{url}/twirp/livekit.RoomService/ListParticipants",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"room": room_name}
        )
        print(f"DEBUG: ListParticipants Status: {response.status_code}")
        print(f"DEBUG: Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_specific_room_id())
