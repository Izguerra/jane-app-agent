from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, generate_agent_id
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.models_db import Agent, PhoneNumber, Communication
from .models import AgentCreate, AgentUpdate
from .logic import broadcast_settings_change
from typing import List

router = APIRouter(tags=["agents-crud"])

@router.get("/", response_model=List[dict])
async def get_agents(request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    wid = get_workspace_context(db, user, request=request)
    agents = db.query(Agent).filter(Agent.workspace_id == wid).all()
    # Logic to flatten settings would go here as in original
    return [a.__dict__ for a in agents]

@router.get("/{agent_id}")
async def get_agent(agent_id: str, request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    wid = get_workspace_context(db, user, request=request)
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == wid).first()
    if not agent: raise HTTPException(status_code=404)
    return agent

@router.post("/")
async def create_agent(agent_data: AgentCreate, request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    wid = get_workspace_context(db, user, request=request)
    new_agent = Agent(id=generate_agent_id(), workspace_id=wid, **agent_data.model_dump(exclude={"phone_number_id"}))
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    await broadcast_settings_change(wid)
    return new_agent

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    wid = get_workspace_context(db, user, request=request)
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == wid).first()
    if not agent: raise HTTPException(status_code=404)
    # Manual cleanup as in original...
    db.delete(agent)
    db.commit()
    await broadcast_settings_change(wid)
    return {"status": "success"}
