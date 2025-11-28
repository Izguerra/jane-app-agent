from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from backend.settings_store import get_settings, save_settings

router = APIRouter(prefix="/settings", tags=["agent-settings"])

# Store for SSE clients
settings_listeners = set()

class AgentSettingsUpdate(BaseModel):
    voice_id: Optional[str] = None
    language: Optional[str] = None
    prompt_template: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/options")
async def get_agent_options():
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy (OpenAI)"},
            {"id": "echo", "name": "Echo (OpenAI)"},
            {"id": "fable", "name": "Fable (OpenAI)"},
            {"id": "onyx", "name": "Onyx (OpenAI)"},
            {"id": "nova", "name": "Nova (OpenAI)"},
            {"id": "shimmer", "name": "Shimmer (OpenAI)"},
            # ElevenLabs examples - using real Voice IDs
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (ElevenLabs)"},
            {"id": "29vD33N1CtxCmqQRPOHJ", "name": "Drew (ElevenLabs)"},
            {"id": "2EiwWnXFnvU5JabPnv8n", "name": "Clyde (ElevenLabs)"},
            {"id": "zrHiDhphv9ZnVXBqCLjf", "name": "Mimi (ElevenLabs)"},
        ],
        "languages": [
            {"id": "auto", "name": "Auto Detection (Multilingual)"},
            {"id": "en", "name": "English"},
            {"id": "es", "name": "Spanish"},
            {"id": "fr", "name": "French"},
            {"id": "de", "name": "German"},
            {"id": "it", "name": "Italian"},
            {"id": "pt", "name": "Portuguese"},
            {"id": "nl", "name": "Dutch"},
            {"id": "ja", "name": "Japanese"},
        ]
    }

@router.get("")
async def get_agent_settings():
    return get_settings()

@router.put("")
async def update_agent_settings(settings: AgentSettingsUpdate):
    # Filter out None values
    update_data = settings.model_dump(exclude_none=True)
    save_settings(update_data)
    
    # Notify all SSE listeners
    await broadcast_settings_change()
    
    return {"status": "success", "data": get_settings()}

@router.get("/stream")
async def settings_stream():
    """Server-Sent Events endpoint for settings change notifications"""
    async def event_generator():
        queue = asyncio.Queue()
        settings_listeners.add(queue)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            
            while True:
                try:
                    # Wait for message with timeout for keepalive
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            settings_listeners.discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )

async def broadcast_settings_change():
    """Broadcast settings change to all connected SSE clients"""
    message = {
        "type": "settings_changed",
        "data": get_settings()
    }
    
    # Send to all listeners
    disconnected = set()
    for queue in settings_listeners:
        try:
            await queue.put(message)
        except Exception:
            disconnected.add(queue)
    
    # Clean up disconnected listeners
    for queue in disconnected:
        settings_listeners.discard(queue)
