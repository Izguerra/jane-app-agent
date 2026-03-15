from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import stripe
import os
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.models_db import Agent
from .models import AgentCreate # For type hinting if needed

router = APIRouter(prefix="/agents", tags=["agents-logic"])

settings_listeners = set()

@router.post("/enhance-soul")
async def enhance_agent_soul(current_soul: str, user: AuthUser = Depends(get_current_user)):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    res = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Expand soul description."}, {"role": "user", "content": current_soul}]
    )
    return {"enhanced_soul": res.choices[0].message.content.strip()}

@router.get("/active-default")
async def get_active_default_agent(request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    wid = get_workspace_context(db, user, request=request)
    agent = db.query(Agent).filter(Agent.workspace_id == wid, Agent.is_active == True).order_by(Agent.is_orchestrator.desc()).first()
    return {"id": agent.id if agent else None, "name": agent.name if agent else "No Active Agent"}

@router.get("/stream")
async def settings_stream():
    async def event_generator():
        q = asyncio.Queue()
        settings_listeners.add(q)
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                msg = await q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        finally: settings_listeners.discard(q)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def broadcast_settings_change(workspace_id: str):
    msg = {"type": "agents_updated", "workspaceId": workspace_id}
    for q in list(settings_listeners):
        await q.put(msg)
