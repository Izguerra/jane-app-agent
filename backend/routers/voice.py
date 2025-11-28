from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import json
from livekit import api
from backend.settings_store import get_settings

router = APIRouter(prefix="/voice", tags=["voice"])

class TokenRequest(BaseModel):
    room_name: str
    participant_name: str

import uuid

@router.get("/token")
async def get_token(room_name: str = None, participant_name: str = "user-1"):
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not room_name:
        room_name = f"room-{str(uuid.uuid4())[:8]}"

    if not api_key or not api_secret or not livekit_url:
        missing = []
        if not api_key:
            missing.append("LIVEKIT_API_KEY")
        if not api_secret:
            missing.append("LIVEKIT_API_SECRET")
        if not livekit_url:
            missing.append("LIVEKIT_URL")
        
        raise HTTPException(
            status_code=503,
            detail=f"LiveKit is not configured. Missing environment variables: {', '.join(missing)}"
        )

    grant = api.VideoGrants(room_join=True, room=room_name)
    
    # Generate unique identity to avoid conflicts on reconnection
    unique_identity = f"user-{str(uuid.uuid4())[:8]}"
    
    # Configure agent dispatch
    room_config = api.RoomConfiguration(
        agents=[
            api.RoomAgentDispatch(agent_name="jane-voice-agent")
        ]
    )
    
    token = (api.AccessToken(api_key, api_secret)
             .with_grants(grant)
             .with_identity(unique_identity)
             .with_name(participant_name)
             .with_room_config(room_config)
             # Pass settings as metadata to the token/room so the agent can read it immediately
             .with_metadata(json.dumps(get_settings())) 
             )
    
    return {
        "token": token.to_jwt(),
        "url": livekit_url
    }
