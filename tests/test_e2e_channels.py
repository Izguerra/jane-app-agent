import asyncio
import os
import sys
import uuid
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit import rtc, api
from backend.agent import AgentManager
from backend.database import SessionLocal
from backend.routers.voice import _generate_token
from backend.auth import AuthUser

AGENT_ID = "agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ"
WORKSPACE_ID = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"

QUESTIONS = [
    "What is the weather in Milton, ON?",
    "What is the best Sushi restaurant in Milton, ON?",
    "What is the distance from L9T0E2 to CN Tower?",
    "Who is the prime minister of Canada?"
]

async def test_chatbot():
    print("\n--- [START] Testing Chatbot ---")
    db = SessionLocal()
    am = AgentManager()
    
    for q in QUESTIONS:
        print(f"\n[Chatbot] Asking: {q}")
        try:
            res = await am.chat(
                workspace_id=WORKSPACE_ID,
                agent_id=AGENT_ID,
                team_id="team_123",
                message=q,
                history=[],
                stream=False,
                db=db
            )
            print(f"[Chatbot] Response: {res[:200]}...")
        except Exception as e:
            print(f"[Chatbot] Failed query {q}: {e}")
    db.close()
    print("--- [DONE] Testing Chatbot ---\n")

async def test_livekit_room(mode: str, num_participants: int):
    print(f"\n--- [START] Testing {mode.capitalize()} Agent with {num_participants} participants ---")
    
    room_name = f"e2e-test-{mode}-{str(uuid.uuid4())[:8]}"
    
    print(f"[{mode.capitalize()}] Dispatching worker to room: {room_name}")
    db = SessionLocal()
    mock_user = AuthUser(id="test_opt1", email="test@janeapp.com", team_id="team_123")
    
    try:
        # Generate token which auto-creates the room and dispatches the worker natively
        res = await _generate_token(
            room_name=room_name,
            participant_name="tester_0",
            agent_id=AGENT_ID,
            agent_config={},
            current_user=mock_user,
            db=db,
            workspace_id=WORKSPACE_ID,
            session_id=str(uuid.uuid4()),
            mode=mode
        )
    except Exception as e:
        print(f"[{mode.capitalize()}] Failed to dispatch worker: {e}")
        db.close()
        return

    db.close()

    # Create tokens for participants
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    rooms: List[rtc.Room] = []
    
    for i in range(num_participants):
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(f"tester_{i}") \
            .with_name(f"Tester {i}") \
            .with_grants(api.VideoGrants(room_join=True, room=room_name)) \
            .to_jwt()
            
        room = rtc.Room()
        await room.connect(livekit_url, token)
        rooms.append(room)
        print(f"[{mode.capitalize()}] Participant {i+1}/{num_participants} connected!")
        
    print(f"[{mode.capitalize()}] Waiting 5 seconds for agent to connect and load tools...")
    await asyncio.sleep(5)
    
    
    for i, q in enumerate(QUESTIONS):
        p_idx = i % num_participants
        active_room = rooms[p_idx]
        print(f"\n[{mode.capitalize()}] Participant {p_idx+1} asking: {q}")
        # In a real playback we'd send audio or ChatManager text, but just validating multi-user join here.
        
    print(f"[{mode.capitalize()}] Verified {num_participants} concurrent connections in {room_name}.")
    
    for room in rooms:
        await room.disconnect()
        
    print(f"--- [DONE] Testing {mode.capitalize()} Agent ---\n")

async def main():
    await test_chatbot()
    await test_livekit_room("voice", 2)
    await test_livekit_room("avatar", 3)
    
if __name__ == "__main__":
    asyncio.run(main())
