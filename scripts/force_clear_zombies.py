import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from livekit import api
from dotenv import load_dotenv

async def cleanup_all_rooms():
    load_dotenv()
    lk_url = os.environ.get("LIVEKIT_URL")
    lk_key = os.environ.get("LIVEKIT_API_KEY")
    lk_secret = os.environ.get("LIVEKIT_API_SECRET")
    
    print(f"URL: {lk_url}")
    print(f"Key format valid: {lk_key.startswith('API') if lk_key else False}")

    if not (lk_url and lk_key):
        print("Missing LiveKit credentials")
        return

    lkapi = api.LiveKitAPI(lk_url, lk_key, lk_secret)
    try:
        rooms_resp = await lkapi.room.list_rooms(api.ListRoomsRequest())
        print(f"Total rooms found in API: {len(rooms_resp.rooms)}")
        for r in rooms_resp.rooms:
            print(f"- {r.name}")
    except Exception as e:
        print(f"LiveKit API Error: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(cleanup_all_rooms())
