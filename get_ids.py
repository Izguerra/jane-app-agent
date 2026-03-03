import asyncio
import os
import json
from livekit import api
from dotenv import load_dotenv

load_dotenv()
async def get_rooms():
    lkapi = api.LiveKitAPI(os.getenv("LIVEKIT_URL"), os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
    req = api.ListRoomsRequest()
    rooms = await lkapi.room.list_rooms(req)
    print(f"Total active/recent rooms: {len(rooms.rooms)}")
    
    for r in rooms.rooms:
        if "toggle-test-" in r.name:
            print(f"Room Name: {r.name} | Room ID: {r.sid}")
            if r.metadata:
                try:
                    meta = json.loads(r.metadata)
                    if "tavus_conversation_id" in meta:
                         print(f"   -> Tavus Conversation ID: {meta['tavus_conversation_id']}")
                    if "mode" in meta:
                         print(f"   -> Mode: {meta['mode']}")
                except:
                    pass
    
    await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(get_rooms())
