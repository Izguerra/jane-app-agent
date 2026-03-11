from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Workspace, Agent

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
async def get_settings(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Get workspace for user
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    return {
        "workspace_id": workspace.id,
        "team_id": workspace.team_id,
        # Add other settings as needed by frontend
    }

@router.get("/stream")
async def stream_settings(
    current_user: AuthUser = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    import asyncio
    import json
    
    async def event_generator():
        try:
            # Initial connection message
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                # Keep alive
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except asyncio.CancelledError:
            pass
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

from pydantic import BaseModel
from backend.lib.translation import translate_text

class TranslateRequest(BaseModel):
    text: str
    target_language: str

@router.post("/translate")
async def translate(
    request: TranslateRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    translated = translate_text(request.text, request.target_language)
    return {"translated_text": translated}
