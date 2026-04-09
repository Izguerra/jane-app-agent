import os
import asyncio
from livekit import api
from dotenv import load_dotenv

async def cleanup_specific_rooms():
    load_dotenv()
    
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([livekit_url, api_key, api_secret]):
        print("ERROR: Missing LiveKit credentials in .env")
        return

    print(f"Connecting to LiveKit: {livekit_url}")
    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
    
    # Names from user's screenshot
    target_names = [
        "agent-session-agnt_000-avatar",
        "agent-session-agnt_000-voice"
    ]
    
    try:
        # 1. Try listing ALL rooms again
        print("Listing all rooms...")
        rooms_res = await lkapi.room.list_rooms(api.ListRoomsRequest())
        print(f"Total rooms seen by API: {len(rooms_res.rooms)}")
        for r in rooms_res.rooms:
            print(f" - {r.name} (Active: {r.num_participants})")

        # 2. Force delete targeted names
        for name in target_names:
            print(f"Attempting to force delete: {name}")
            try:
                await lkapi.room.delete_room(api.DeleteRoomRequest(room=name))
                print(f"Successfully deleted {name}")
            except Exception as e:
                print(f"Failed to delete {name}: {e}")
                
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(cleanup_specific_rooms())
