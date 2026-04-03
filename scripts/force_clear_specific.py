import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from livekit import api
from dotenv import load_dotenv

async def force_delete_specific():
    load_dotenv()
    lk_url = os.environ.get("LIVEKIT_URL")
    if lk_url and lk_url.startswith("ws"):
        lk_url = lk_url.replace("ws", "http", 1)
        
    lk_key = os.environ.get("LIVEKIT_API_KEY")
    lk_secret = os.environ.get("LIVEKIT_API_SECRET")
    
    lkapi = api.LiveKitAPI(lk_url, lk_key, lk_secret)
    room_name = "agent-session-agnt_000-avatar"
    
    print(f"Attempting to force delete room: {room_name}")
    try:
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
        print(f"Successfully deleted {room_name}")
    except Exception as e:
        print(f"Failed to delete {room_name}: {e}")

    await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(force_delete_specific())
