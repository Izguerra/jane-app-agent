#!/usr/bin/env python3
"""
Test script to verify LiveKit room creation and agent dispatch configuration.
Run this to diagnose why the agent isn't receiving job dispatches.
"""
import os
import asyncio
from dotenv import load_dotenv
from livekit.api import RoomServiceClient, CreateRoomRequest, ListRoomsRequest, DeleteRoomRequest, RoomAgentDispatch

load_dotenv()

async def test_livekit_config():
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    print("=" * 60)
    print("LiveKit Configuration Test")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print(f"   LIVEKIT_API_KEY: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"   LIVEKIT_API_SECRET: {'✓ Set' if api_secret else '✗ Missing'}")
    print(f"   LIVEKIT_URL: {livekit_url if livekit_url else '✗ Missing'}")
    
    if not all([api_key, api_secret, livekit_url]):
        print("\n❌ Missing required environment variables!")
        return
    
    # Test room creation with agent dispatch
    print("\n2. Testing Room Creation with Agent Dispatch:")
    try:
        svc = RoomServiceClient(livekit_url, api_key, api_secret)
        
        test_room_name = "test-dispatch-room"
        print(f"   Creating room: {test_room_name}")
        
        room = await svc.create_room(CreateRoomRequest(
            name=test_room_name,
            empty_timeout=60,
            max_participants=2,
            agents=[
                RoomAgentDispatch(agent_name="supaagent-voice-agent")
            ]
        ))
        
        print(f"   ✓ Room created successfully: {room.name}")
        print(f"   Room SID: {room.sid}")
        
        # List rooms to verify
        print("\n3. Listing Active Rooms:")
        rooms = await svc.list_rooms(ListRoomsRequest())
        for r in rooms.rooms:
            print(f"   - {r.name} (SID: {r.sid}, Participants: {r.num_participants})")
        
        # Clean up test room
        print(f"\n4. Cleaning up test room...")
        await svc.delete_room(DeleteRoomRequest(room=test_room_name))
        print(f"   ✓ Test room deleted")
        
        print("\n" + "=" * 60)
        print("✅ LiveKit configuration is WORKING!")
        print("=" * 60)
        print("\nIf the voice agent still isn't connecting, the issue is likely:")
        print("1. The agent worker isn't registered with the correct name")
        print("2. The LiveKit server has stale worker registrations")
        print("3. The token generation is using a different LiveKit URL")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis indicates a LiveKit configuration or connectivity issue.")

if __name__ == "__main__":
    asyncio.run(test_livekit_config())
