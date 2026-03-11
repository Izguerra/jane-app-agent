import os
import asyncio
from livekit import api

async def main():
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    # Needs to match the env vars or read from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    if not api_key:
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        livekit_url = os.getenv("LIVEKIT_URL")

    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
    try:
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest())
        print(f"Found {len(rooms.rooms)} active rooms.")
        for room in rooms.rooms:
            print(f"Room: {room.name}")
            req = api.ListParticipantsRequest(room=room.name)
            participants = await lkapi.room.list_participants(req)
            print(f"  Participants ({len(participants.participants)}):")
            for p in participants.participants:
                print(f"    - {p.identity} (is_publisher: {p.is_publisher})")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
