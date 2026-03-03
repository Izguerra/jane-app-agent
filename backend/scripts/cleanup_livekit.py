import os
import asyncio
import json
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def cleanup():
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        print("Missing LiveKit credentials in .env")
        return

    print(f"Connecting to LiveKit: {livekit_url}")
    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)

    try:
        # List all rooms
        rooms_res = await lkapi.room.list_rooms(api.ListRoomsRequest())
        rooms = rooms_res.rooms

        if not rooms:
            print("No active rooms found.")
            return

        print(f"Found {len(rooms)} rooms. Checking for zombies...")

        for room in rooms:
            print(f"Room: {room.name} | Participants: {room.num_participants} | Created: {room.creation_time}")
            
            # Decision logic: 
            # 1. Rooms older than 1 hour are definitely zombies for a preview/test environment
            # 2. Rooms with 'toggle-test' or 'room-' prefix are targets
            
            should_delete = False
            if room.num_participants == 0:
                should_delete = True
                print(f"  -> Target for deletion: 0 participants")
            elif "toggle-test" in room.name or room.name.startswith("room-"):
                # If it's a test room and has been active a while, or we just want a clean slate
                should_delete = True
                print(f"  -> Target for deletion: Test/Preview room")
            
            if should_delete:
                try:
                    await lkapi.room.delete_room(api.DeleteRoomRequest(room=room.name))
                    print(f"  [SUCCESS] Deleted room: {room.name}")
                except Exception as de:
                    print(f"  [ERROR] Failed to delete room {room.name}: {de}")

    except Exception as e:
        print(f"Cleanup failed: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(cleanup())
