from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, generate_agent_id
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.models_db import Agent, PhoneNumber, Communication
from .models import AgentCreate, AgentUpdate, AgentResponse
from .logic import broadcast_settings_change
from typing import List, Dict, Any, Optional
import json

router = APIRouter(prefix="/agents", tags=["agents-crud"])

def flatten_agent(agent: Agent) -> Dict[str, Any]:
    """Helper to merge the 'settings' JSON into the top-level dict for the API."""
    data = {
        "id": agent.id,
        "workspace_id": agent.workspace_id,
        "name": agent.name,
        "voice_id": agent.voice_id,
        "language": agent.language,
        "prompt_template": agent.prompt_template,
        "welcome_message": agent.welcome_message,
        "is_orchestrator": agent.is_orchestrator,
        "is_active": agent.is_active,
        "description": agent.description,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "phone_numbers": [
            {
                "id": p.id,
                "phone_number": p.phone_number,
                "friendly_name": p.friendly_name,
                "country_code": p.country_code
            } for p in agent.phone_numbers
        ] if hasattr(agent, 'phone_numbers') else []
    }
    
    # Merge settings JSON
    if agent.settings:
        settings_data = agent.settings if isinstance(agent.settings, dict) else json.loads(agent.settings)
        data.update(settings_data)
        
    return data

@router.get("", response_model=List[AgentResponse])
async def get_agents(
    request: Request, 
    workspace_id: Optional[str] = Query(None, alias="workspace_id"),
    db: Session = Depends(get_db), 
    user: AuthUser = Depends(get_current_user)
):
    wid = get_workspace_context(db, user, workspace_id=workspace_id, request=request)
    agents = db.query(Agent).options(joinedload(Agent.phone_numbers)).filter(Agent.workspace_id == wid).all()
    return [flatten_agent(a) for a in agents]

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str, 
    request: Request, 
    workspace_id: Optional[str] = Query(None, alias="workspace_id"),
    db: Session = Depends(get_db), 
    user: AuthUser = Depends(get_current_user)
):
    wid = get_workspace_context(db, user, workspace_id=workspace_id, request=request)
    agent = db.query(Agent).options(joinedload(Agent.phone_numbers)).filter(Agent.id == agent_id, Agent.workspace_id == wid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return flatten_agent(agent)

@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate, 
    request: Request, 
    workspace_id: Optional[str] = Query(None, alias="workspace_id"),
    db: Session = Depends(get_db), 
    user: AuthUser = Depends(get_current_user)
):
    wid = get_workspace_context(db, user, workspace_id=workspace_id, request=request)
    
    # Separate base fields from settings fields
    base_fields = {"name", "voice_id", "language", "prompt_template", "welcome_message", "is_orchestrator", "is_active", "description"}
    data_dict = agent_data.model_dump()
    
    base_values = {k: v for k, v in data_dict.items() if k in base_fields}
    settings_values = {k: v for k, v in data_dict.items() if k not in base_fields and k != "phone_number_id"}
    
    new_agent = Agent(
        id=generate_agent_id(),
        workspace_id=wid,
        settings=settings_values,
        **base_values
    )
    
    db.add(new_agent)
    
    # Handle phone number assignment if provided
    if agent_data.phone_number_id:
        phone = db.query(PhoneNumber).filter(PhoneNumber.id == agent_data.phone_number_id, PhoneNumber.workspace_id == wid).first()
        if phone:
            phone.agent_id = new_agent.id
            
    db.commit()
    db.refresh(new_agent)
    
    await broadcast_settings_change(wid)
    return flatten_agent(new_agent)

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str, 
    agent_data: AgentUpdate, 
    request: Request, 
    workspace_id: Optional[str] = Query(None, alias="workspace_id"),
    db: Session = Depends(get_db), 
    user: AuthUser = Depends(get_current_user)
):
    wid = get_workspace_context(db, user, workspace_id=workspace_id, request=request)
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == wid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    base_fields = {"name", "voice_id", "language", "prompt_template", "welcome_message", "is_orchestrator", "is_active", "description"}
    update_dict = agent_data.model_dump(exclude_unset=True)
    
    current_settings = agent.settings if isinstance(agent.settings, dict) else (json.loads(agent.settings) if agent.settings else {})
    
    for key, value in update_dict.items():
        if key in base_fields:
            setattr(agent, key, value)
        elif key == "phone_number_id":
            # Update phone number assignment
            # First, clear existing phone numbers for this agent if we want a 1:1, or just assign new one
            # The original logic assigned the phone.agent_id
            phone = db.query(PhoneNumber).filter(PhoneNumber.id == value, PhoneNumber.workspace_id == wid).first()
            if phone:
                phone.agent_id = agent.id
        else:
            # Standardization: Normalize camelCase to snake_case for known keys
            snake_key = key
            if key == "openClawInstanceId": snake_key = "open_claw_instance_id"
            if key == "tavusReplicaId": snake_key = "tavus_replica_id"
            if key == "anamPersonaId": snake_key = "anam_persona_id"
            if key == "avatarProvider": snake_key = "avatar_provider"
            if key == "avatarVoiceId": snake_key = "avatar_voice_id"
            if key == "useTavusAvatar": snake_key = "use_tavus_avatar"
            
            # Personal Profile Field Mapping
            if key == "ownerName": snake_key = "owner_name"
            if key == "personalLocation": snake_key = "personal_location"
            if key == "personalTimezone": snake_key = "personal_timezone"
            if key == "favoriteFoods": snake_key = "favorite_foods"
            if key == "favoriteRestaurants": snake_key = "favorite_restaurants"
            if key == "favoriteMusic": snake_key = "favorite_music"
            if key == "favoriteActivities": snake_key = "favorite_activities"
            if key == "otherInterests": snake_key = "other_interests"
            if key == "personalLikes": snake_key = "personal_likes"
            if key == "personalDislikes": snake_key = "personal_dislikes"
            
            current_settings[snake_key] = value
            
            # Clean up old casing if it exists in the dict
            if snake_key != key:
                current_settings.pop(key, None)
            
    agent.settings = current_settings
    
    # Special logic for Vector Sync if soul changed
    if "soul" in update_dict and update_dict["soul"]:
        try:
            from backend.services.vector_sync import sync_agent_soul
            sync_agent_soul(wid, agent.id, update_dict["soul"])
        except Exception as e:
            print(f"Failed to sync soul to Pinecone: {e}")

    db.commit()
    db.refresh(agent)
    
    await broadcast_settings_change(wid)
    return flatten_agent(agent)

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str, 
    request: Request, 
    workspace_id: Optional[str] = Query(None, alias="workspace_id"),
    db: Session = Depends(get_db), 
    user: AuthUser = Depends(get_current_user)
):
    wid = get_workspace_context(db, user, workspace_id=workspace_id, request=request)
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == wid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Cleanup phone number assignments
    db.query(PhoneNumber).filter(PhoneNumber.agent_id == agent.id).update({"agent_id": None})
    
    db.delete(agent)
    db.commit()
    
    await broadcast_settings_change(wid)
    return {"status": "success"}
