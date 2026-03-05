
import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def list_workers():
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    print(f"Connecting to {url}...")
    lk_api = api.LiveKitAPI(url, key, secret)
    
    try:
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        print(f"Active rooms: {len(rooms.rooms)}")
        for i, room in enumerate(rooms.rooms):
            print(f"{i+1}. {room.name} | Participants: {room.num_participants} | Metadata: {room.metadata[:100]}...")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error listing: {e}")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(list_workers())
