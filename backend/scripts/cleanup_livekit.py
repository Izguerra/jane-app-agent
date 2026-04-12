import os
import asyncio
import json
from livekit import api
from dotenv import load_dotenv

async def cleanup_rooms():
    load_dotenv()
    
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([livekit_url, api_key, api_secret]):
        print("ERROR: Missing LiveKit credentials in .env")
        return

    print(f"Connecting to LiveKit: {livekit_url}")
    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
    
    try:
        # List all rooms
        rooms_res = await lkapi.room.list_rooms(api.ListRoomsRequest())
        rooms = rooms_res.rooms
        
        print(f"Found {len(rooms)} total rooms.")
        
        deleted_count = 0
        for room in rooms:
            if room.name.startswith("agent-session-"):
                print(f"Deleting zombie room: {room.name} (Participants: {room.num_participants}, Duration: {room.creation_time})")
                try:
                    await lkapi.room.delete_room(api.DeleteRoomRequest(room=room.name))
                    deleted_count += 1
                except Exception as e:
                    print(f"  Failed to delete {room.name}: {e}")
        
        print(f"Successfully deleted {deleted_count} zombie rooms.")
        
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(cleanup_rooms())
