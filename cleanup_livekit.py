import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def cleanup():
    url = os.getenv('LIVEKIT_URL')
    api_key = os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LIVEKIT_API_SECRET')
    
    print(f"Connecting to: {url}")
    lkapi = api.LiveKitAPI(url, api_key, api_secret)
    
    try:
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest())
        print(f"Found {len(rooms.rooms)} rooms.")
        for r in rooms.rooms:
            print(f"Deleting room: {r.name}")
            try:
                await lkapi.room.delete_room(api.DeleteRoomRequest(room=r.name))
            except Exception as re:
                print(f"Failed to delete {r.name}: {re}")
                
        # Also list and delete dispatches
        # Not strictly needed since room deletion kills dispatches, but good for cleanup
    finally:
        await lkapi.aclose()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(cleanup())
