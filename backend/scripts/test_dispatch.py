
import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def check_dispatch():
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    print(f"Connecting to {url}...")
    lk_api = api.LiveKitAPI(url, key, secret)
    
    try:
        # Check for registered workers (Available in LiveKit Cloud dashboard mostly, but let's see what we can find)
        # Service objects usually have some info.
        
        # More useful: Try to create a room with agent dispatch and see if it errors
        room_name = f"test-dispatch-{os.urandom(2).hex()}"
        target_agent = "supaagent-voice-agent-v2"
        
        print(f"Testing dispatch for agent: {target_agent}")
        try:
            room = await lk_api.room.create_room(api.CreateRoomRequest(
                name=room_name,
                agents=[api.RoomAgentDispatch(agent_name=target_agent)]
            ))
            print(f"Room {room_name} created successfully with dispatch.")
        except Exception as e:
            print(f"Error creating room with dispatch: {e}")
            
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(check_dispatch())
