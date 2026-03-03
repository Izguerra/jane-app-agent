from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import asyncio
import json
from sqlalchemy.orm import Session
# from backend.settings_store import get_settings, save_settings # Deprecated
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.database import get_db, generate_agent_id
from backend.models_db import (
    Agent, Communication, PhoneNumber, Integration, 
    WorkerTask, AgentSkill, AgentPersonality
)
from backend.lib.translation import translate_text
from sqlalchemy.orm.attributes import flag_modified
from backend.services.vector_sync import sync_agent_soul

router = APIRouter(prefix="/agents", tags=["agents"])

# Store for SSE clients
settings_listeners = set()

class EnhanceSoulRequest(BaseModel):
    current_soul: str

class AgentCreate(BaseModel):
    name: str = "My Agent"
    voice_id: Optional[str] = "alloy"
    language: Optional[str] = "en"
    prompt_template: Optional[str] = "You are a helpful assistant."
    welcome_message: Optional[str] = None
    is_orchestrator: bool = False
    description: Optional[str] = None
    phone_number_id: Optional[str] = None
    allowed_worker_types: Optional[List[str]] = None
    
    # Extended Wizard Fields
    avatar: Optional[str] = None
    primary_function: Optional[str] = None
    conversation_style: Optional[str] = None
    creativity_level: Optional[int] = 50
    response_length: Optional[int] = 50
    proactive_followups: Optional[bool] = True
    
    # Knowledge Base
    business_name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    services: Optional[str] = None
    hours_of_operation: Optional[str] = None
    faq: Optional[str] = None # JSON string
    reference_urls: Optional[str] = None # JSON string
    kb_documents_urls: Optional[List[str]] = None
    
    # Rules
    intent_rules: Optional[str] = None # JSON string
    handoff_message: Optional[str] = None
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    auto_escalate: Optional[bool] = False
    
    # Widget
    deployment_channel: Optional[str] = "web_widget"
    accent_color: Optional[str] = "#3B82F6"
    widget_icon: Optional[str] = "chat"
    widget_icon_url: Optional[str] = None
    widget_position: Optional[str] = "bottom_right"
    remove_branding: Optional[bool] = False
    whitelisted_domains: Optional[str] = None
    is_active: Optional[bool] = True
    tavus_replica_id: Optional[str] = None
    tavusReplicaId: Optional[str] = None
    avatar_voice_id: Optional[str] = None
    avatarVoiceId: Optional[str] = None
    use_tavus_avatar: Optional[bool] = False
    useTavusAvatar: Optional[bool] = False
    openClawInstanceId: Optional[str] = None
    open_claw_instance_id: Optional[str] = None
    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    max_depth: Optional[int] = None

    # Personal Agent Profile Fields
    owner_name: Optional[str] = None
    personal_location: Optional[str] = None
    personal_timezone: Optional[str] = None
    favorite_foods: Optional[str] = None
    favorite_restaurants: Optional[str] = None
    favorite_music: Optional[str] = None
    favorite_activities: Optional[str] = None
    other_interests: Optional[str] = None
    personal_likes: Optional[str] = None
    personal_dislikes: Optional[str] = None
    soul: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    prompt_template: Optional[str] = None
    welcome_message: Optional[str] = None
    is_orchestrator: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    phone_number_id: Optional[str] = None
    allowed_worker_types: Optional[List[str]] = None
    
    # Extended Fields (Same as Create)
    avatar: Optional[str] = None
    primary_function: Optional[str] = None
    conversation_style: Optional[str] = None
    creativity_level: Optional[int] = None
    response_length: Optional[int] = None
    proactive_followups: Optional[bool] = None
    business_name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    services: Optional[str] = None
    hours_of_operation: Optional[str] = None
    faq: Optional[str] = None
    reference_urls: Optional[str] = None
    kb_documents_urls: Optional[List[str]] = None
    intent_rules: Optional[str] = None
    handoff_message: Optional[str] = None
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    auto_escalate: Optional[bool] = None
    deployment_channel: Optional[str] = None
    accent_color: Optional[str] = None
    widget_icon: Optional[str] = None
    widget_icon_url: Optional[str] = None
    widget_position: Optional[str] = None
    remove_branding: Optional[bool] = None
    whitelisted_domains: Optional[str] = None
    tavus_replica_id: Optional[str] = None
    tavusReplicaId: Optional[str] = None
    avatar_voice_id: Optional[str] = None
    avatarVoiceId: Optional[str] = None
    use_tavus_avatar: Optional[bool] = None
    useTavusAvatar: Optional[bool] = None
    openClawInstanceId: Optional[str] = None
    open_claw_instance_id: Optional[str] = None
    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    # Personal Agent Profile Fields
    owner_name: Optional[str] = None
    personal_location: Optional[str] = None
    personal_timezone: Optional[str] = None
    favorite_foods: Optional[str] = None
    favorite_restaurants: Optional[str] = None
    favorite_music: Optional[str] = None
    favorite_activities: Optional[str] = None
    other_interests: Optional[str] = None
    personal_likes: Optional[str] = None
    personal_dislikes: Optional[str] = None
    soul: Optional[str] = None

@router.post("/enhance-soul")
async def enhance_agent_soul(
    data: EnhanceSoulRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """Takes a brief user-provided soul description and expands it into a comprehensive set of persona instructions."""
    import os
    from openai import AsyncOpenAI
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
    client = AsyncOpenAI(api_key=api_key)
    
    # We use structured instruction for the LLM to expand the soul
    system_prompt = """You are an expert prompt engineer and AI architect. 
The user is providing a brief, raw description or a few rules for their Customer Support AI Agent's "Core Identity" (its Soul). 
Your job is to take their brief description and expand it into a highly professional, well-structured, and comprehensive directive.

Guidelines for your rewrite:
1. Make it an actionable set of instructions for an AI (e.g., "You are an energetic sales assistant... Your primary goal is to...").
2. Include elements like Core Objective, Tone & Personality, and absolute Negative Boundaries (what it must NEVER do).
3. Keep it under 200 words. Make it punchy and direct.
4. DO NOT add conversational filler like "Here is your expanded text." Return ONLY the expanded instructions.
5. If the user's input is very short (e.g., "be polite and sell shoes"), flesh it out logically into a professional retail assistant persona.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Fast, cheap, capable enough for this
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the brief description:\n\n{data.current_soul}"}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        enhanced_text = response.choices[0].message.content.strip()
        return {"enhanced_soul": enhanced_text}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to enhance soul: {str(e)}")

@router.get("/active-default")
async def get_active_default_agent(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, request=request)
    
    # Simple logic: First active agent for now, prefer orchestrator
    agent = db.query(Agent).filter(
        Agent.workspace_id == workspace_id,
        Agent.is_active == True
    ).order_by(Agent.is_orchestrator.desc()).first()

    if not agent:
        return {"id": None, "name": "No Active Agent"}
        
    return {"id": agent.id, "name": agent.name}

@router.get("/options")
async def get_agent_options():
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy"},
            {"id": "echo", "name": "Echo"},
            {"id": "fable", "name": "Fable"},
            {"id": "onyx", "name": "Onyx"},
            {"id": "nova", "name": "Nova"},
            {"id": "shimmer", "name": "Shimmer"},
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (ElevenLabs)"},
            {"id": "29vD33N1CtxCmqQRPOHJ", "name": "Drew (ElevenLabs)"},
            {"id": "2EiwWnXFnvU5JabPnv8n", "name": "Clyde (ElevenLabs)"},
            {"id": "zrHiDhphv9ZnVXBqCLjf", "name": "Mimi (ElevenLabs)"},
        ],
        "languages": [
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

@router.get("/{agent_id}/settings")
async def get_agent_settings(
    agent_id: str,
    request: Request,
    translate: bool = False,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, request=request)

    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    settings = {}
    if agent.settings:
        settings = dict(agent.settings)

    # Base fields from root columns ALWAYS take precedence
    base_fields = [
        "name", "voice_id", "language", "prompt_template", "welcome_message",
        "soul", "is_orchestrator", "description", "is_active",
        "owner_name", "personal_location", "personal_timezone", "favorite_foods",
        "favorite_restaurants", "favorite_music", "favorite_activities",
        "other_interests", "personal_likes", "personal_dislikes"
    ]
    for field in base_fields:
        if hasattr(agent, field):
            val = getattr(agent, field)
            if val is not None:
                settings[field] = val
    
    # Add allowed_worker_types separately if present
    print(f"DEBUG: Agent {agent.id} allowed_worker_types in DB: {agent.allowed_worker_types}")
    if agent.allowed_worker_types is not None:
        settings["allowed_worker_types"] = agent.allowed_worker_types
    
    # Ensure it's a list if it made it into settings, or don't set it (let consumer handle default)
    # But better to be explicit:
    if "allowed_worker_types" not in settings and agent.allowed_worker_types is not None:
         settings["allowed_worker_types"] = agent.allowed_worker_types

    # Translate welcome message if requesting translation
    if translate and settings.get("welcome_message") and settings.get("language"):
        settings["welcome_message"] = translate_text(
            settings["welcome_message"], 
            settings["language"]
        )
        
    print(f"DEBUG: Final settings for agent {agent_id}: {settings.keys()}")
    return settings

from sqlalchemy.orm import joinedload
from datetime import datetime

# Move this block from above
# (Already deleted in first chunk)

class AgentPhoneNumberResponse(BaseModel):
    id: str
    phone_number: str
    friendly_name: Optional[str] = None
    country_code: Optional[str] = None

class AgentResponse(AgentCreate):
    id: str
    workspace_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    phone_numbers: List[AgentPhoneNumberResponse] = []


    class Config:
        from_attributes = True

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch a single agent by ID with flattened settings and root precedence."""
    agent = db.query(Agent).options(joinedload(Agent.phone_numbers)).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Verify workspace access from request context if needed, but here we can just check workspace_id
    # get_workspace_context handles getting it from header or db
    from backend.auth import get_workspace_context
    workspace_id = get_workspace_context(db, current_user, request=request)
    if agent.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Dynamic extraction of all root columns
    from sqlalchemy import inspect
    mapper = inspect(Agent)
    response_data = {}
    for column in mapper.attrs:
        # Check if attribute is a column (not a relationship)
        if hasattr(column, 'key'):
            val = getattr(agent, column.key)
            # Serialize datetime for JSON response
            if isinstance(val, datetime):
                response_data[column.key] = val
            else:
                response_data[column.key] = val
    
    # Explicitly add phone_numbers relation
    response_data["phone_numbers"] = agent.phone_numbers

    # Merge settings if they exist, ensuring root fields take precedence
    if agent.settings:
        settings_copy = dict(agent.settings)
        settings_copy.update(response_data)
        response_data = settings_copy
        
    return response_data

@router.get("", response_model=List[AgentResponse])
async def get_agents(
    request: Request,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, workspace_id, request=request)
    

        

    agents = db.query(Agent).options(joinedload(Agent.phone_numbers)).filter(Agent.workspace_id == workspace_id).all()
    
    if not agents:
        # Create defaults logic (omitted for brevity, same as before but simplified)
        pass
        
    # Dynamic extraction setup
    from sqlalchemy import inspect
    mapper = inspect(Agent)
    
    # Transform agents to include settings flattened
    response_agents = []
    for agent in agents:
        agent_dict = {}
        for column in mapper.attrs:
            if hasattr(column, 'key'):
                val = getattr(agent, column.key)
                agent_dict[column.key] = val
        
        # Explicitly add phone_numbers relation
        agent_dict["phone_numbers"] = agent.phone_numbers
        
        # Merge settings if they exist
        if agent.settings:
            # Create a combined dict where root fields take precedence
            settings_copy = dict(agent.settings)
            settings_copy.update(agent_dict)
            agent_dict = settings_copy
            
        response_agents.append(agent_dict)
        
    return response_agents

@router.post("")
async def create_agent(
    agent_data: AgentCreate,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        workspace_id = get_workspace_context(db, current_user, request=request)
        
        # Extract settings fields
        base_fields = {"name", "voice_id", "language", "prompt_template", "welcome_message", "is_orchestrator", "description", "is_active", "phone_number_id", "allowed_worker_types", "soul"}
        settings_data = agent_data.model_dump(exclude=base_fields)
        
        new_agent = Agent(
            id=generate_agent_id(),
            workspace_id=workspace_id,
            name=agent_data.name,
            voice_id=agent_data.voice_id,
            language=agent_data.language,
            prompt_template=agent_data.prompt_template,
            welcome_message=agent_data.welcome_message,
            is_orchestrator=agent_data.is_orchestrator,
            description=agent_data.description,
            is_active=agent_data.is_active,
            allowed_worker_types=agent_data.allowed_worker_types or [], 
            soul=agent_data.soul,
            settings=settings_data # Store extended fields in JSON column
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        if agent_data.phone_number_id:
            from backend.models_db import PhoneNumber
            phone = db.query(PhoneNumber).filter(
                PhoneNumber.id == agent_data.phone_number_id,
                PhoneNumber.workspace_id == workspace_id
            ).first()
            if phone:
                phone.agent_id = new_agent.id
                db.add(phone)
                db.commit()
                
                
        # Auto-provision OpenClaw (DEPRECATED in BYO Model)
        # If users select "OpenClaw", we assume they have connected a worker in Settings.
        # We do NOT auto-provision anymore.
        if new_agent.allowed_worker_types and "openclaw" in new_agent.allowed_worker_types:
            pass # Logic moved to "Connect Instance" flow logic

        await broadcast_settings_change(workspace_id)
        
        # Return flattened response consistently with get_agents
        response_data = {
            "id": new_agent.id,
            "name": new_agent.name,
            "voice_id": new_agent.voice_id,
            "language": new_agent.language,
            "prompt_template": new_agent.prompt_template,
            "welcome_message": new_agent.welcome_message,
            "is_orchestrator": new_agent.is_orchestrator,
            "description": new_agent.description,
            "is_active": new_agent.is_active,
            "soul": new_agent.soul,
            "created_at": new_agent.created_at,
            "updated_at": new_agent.updated_at,
            "allowed_worker_types": new_agent.allowed_worker_types,
        }
        
        # Sync Soul to Pinecone if present
        if new_agent.soul:
            try:
                sync_agent_soul(workspace_id, new_agent.id, new_agent.soul)
            except Exception as e:
                print(f"Warning: Failed to sync soul to Pinecone: {e}")
        if new_agent.settings:
            # Create a combined dict where actual root fields take precedence
            settings_copy = dict(new_agent.settings)
            settings_copy.update(response_data)
            response_data = settings_copy
            
        return response_data
    except Exception as e:
        import traceback
        print("CRITICAL ERROR in create_agent:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    settings: AgentUpdate,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # First, find the agent by ID
        agent_obj = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent_obj:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Then verify user has access to this agent's workspace via team_id
        # We allow the update if it belongs to the user's active team workspace
        workspace_id = get_workspace_context(db, current_user, request=request)
        if agent_obj.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Access denied to this agent")
    
        
        update_data = settings.model_dump(exclude_none=True)
        
        # Identify base fields vs settings fields
        base_fields = {"name", "voice_id", "language", "prompt_template", "welcome_message", "is_orchestrator", "description", "is_active", "phone_number_id", "allowed_worker_types", "soul"}
        
        current_settings = agent_obj.settings or {}
        
        print(f"DEBUG: update_data keys: {list(update_data.keys())}")
        for key, value in update_data.items():
            if key == "phone_number_id":
                 continue
            
            if key in base_fields:
                print(f"DEBUG: Updating base field {key} to {str(value)[:50]}...")
                setattr(agent_obj, key, value)
                # Cleanup: remove from settings JSON if it exists there to prevent conflicts
                current_settings.pop(key, None)
            else:
                # Standardization loop: Normalize camelCase to snake_case for known keys
                snake_key = key
                if key == "openClawInstanceId": snake_key = "open_claw_instance_id"
                if key == "tavusReplicaId": snake_key = "tavus_replica_id"
                if key == "avatarVoiceId": snake_key = "avatar_voice_id"
                if key == "useTavusAvatar": snake_key = "use_tavus_avatar"
                
                # New Personal Profile Field Mapping
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
                
                # Clean up old casing if it exists
                if snake_key == "open_claw_instance_id": current_settings.pop("openClawInstanceId", None)
                if snake_key == "tavus_replica_id": current_settings.pop("tavusReplicaId", None)
                if snake_key == "avatar_voice_id": current_settings.pop("avatarVoiceId", None)
                if snake_key == "use_tavus_avatar": current_settings.pop("useTavusAvatar", None)
                if snake_key == "owner_name": current_settings.pop("ownerName", None)
                if snake_key == "personal_location": current_settings.pop("personalLocation", None)
                if snake_key == "personal_timezone": current_settings.pop("personalTimezone", None)
                if snake_key == "favorite_foods": current_settings.pop("favoriteFoods", None)
                if snake_key == "favorite_restaurants": current_settings.pop("favoriteRestaurants", None)
                if snake_key == "favorite_music": current_settings.pop("favoriteMusic", None)
                if snake_key == "favorite_activities": current_settings.pop("favoriteActivities", None)
                if snake_key == "other_interests": current_settings.pop("otherInterests", None)
                if snake_key == "personal_likes": current_settings.pop("personalLikes", None)
                if snake_key == "personal_dislikes": current_settings.pop("personalDislikes", None)
                
        # Force change detection
        agent_obj.settings = dict(current_settings)
        flag_modified(agent_obj, "settings")
        # Ensure allowed_worker_types is also flagged if updated
        if "allowed_worker_types" in update_data:
            flag_modified(agent_obj, "allowed_worker_types")
        
        # SAFEGUARD: If OpenClaw instance is configured, ensure the capability is enabled
        openclaw_id = current_settings.get("open_claw_instance_id")
        if openclaw_id:
            current_workers = agent_obj.allowed_worker_types or []
            if "openclaw" not in current_workers:
                new_workers = list(current_workers) + ["openclaw"]
                agent_obj.allowed_worker_types = new_workers
                flag_modified(agent_obj, "allowed_worker_types")
            
        if "phone_number_id" in update_data:
            from backend.models_db import PhoneNumber
            phone_id = update_data["phone_number_id"]
            
            existing = db.query(PhoneNumber).filter(PhoneNumber.agent_id == agent_obj.id).all()
            for p in existing:
                p.agent_id = None
                db.add(p)
                
            if phone_id:
                phone = db.query(PhoneNumber).filter(
                    PhoneNumber.id == phone_id,
                    PhoneNumber.workspace_id == workspace_id
                ).first()
                if phone:
                    phone.agent_id = agent_obj.id
                    db.add(phone)
                db.commit()
    
        db.add(agent_obj)
        db.commit()
        db.refresh(agent_obj)
    
        await broadcast_settings_change(workspace_id)
        
        # Return flattened response consistently
        response_data = {
            "id": agent_obj.id,
            "name": agent_obj.name,
            "voice_id": agent_obj.voice_id,
            "language": agent_obj.language,
            "prompt_template": agent_obj.prompt_template,
            "welcome_message": agent_obj.welcome_message,
            "is_orchestrator": agent_obj.is_orchestrator,
            "description": agent_obj.description,
            "is_active": agent_obj.is_active,
            "soul": agent_obj.soul,
            "created_at": agent_obj.created_at,
            "updated_at": agent_obj.updated_at,
            "allowed_worker_types": agent_obj.allowed_worker_types,
        }
        
        # Sync Soul to Pinecone if updated
        if "soul" in update_data and agent_obj.soul:
            try:
                sync_agent_soul(workspace_id, agent_obj.id, agent_obj.soul)
            except Exception as e:
                print(f"Warning: Failed to sync soul to Pinecone: {e}")
        if agent_obj.settings:
            # Create a combined dict where actual root fields take precedence
            settings_copy = dict(agent_obj.settings)
            settings_copy.update(response_data)
            response_data = settings_copy
            
        return response_data
    except Exception as e:
        import traceback
        print("CRITICAL ERROR in update_agent:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, request=request)
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Manual cleanup of references (to avoid foreign key constraint errors)
    # These are nullable FKs, so we set them to NULL to preserve history
    db.query(Communication).filter(Communication.agent_id == agent_id).update({Communication.agent_id: None}, synchronize_session=False)
    db.query(PhoneNumber).filter(PhoneNumber.agent_id == agent_id).update({PhoneNumber.agent_id: None}, synchronize_session=False)
    db.query(Integration).filter(Integration.agent_id == agent_id).update({Integration.agent_id: None}, synchronize_session=False)
    db.query(WorkerTask).filter(WorkerTask.dispatched_by_agent_id == agent_id).update({WorkerTask.dispatched_by_agent_id: None}, synchronize_session=False)
    
    # Explicitly delete child entities
    db.query(AgentSkill).filter(AgentSkill.agent_id == agent_id).delete(synchronize_session=False)
    db.query(AgentPersonality).filter(AgentPersonality.agent_id == agent_id).delete(synchronize_session=False)

    # Flush updates to DB before deleting the agent
    db.flush()

    db.delete(agent)
    db.commit()
    
    # Notify listeners
    await broadcast_settings_change(workspace_id)
    
    return {"status": "success"}

@router.get("/stream")
async def settings_stream():
    """Server-Sent Events endpoint for settings change notifications"""
    # TODO: Add authentication and workspace filtering here
    # For now, this simple implementation broadcasts to all
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

async def broadcast_settings_change(clinic_id: str = None):
    """Broadcast settings change to all connected SSE clients"""
    # In a real app, we'd only broadcast to clients in the same clinic
    # For agents, we might want to send the Updated List of agents?
    # Or just a "trigger" to refetch.
    
    message = {
        "type": "agents_updated",
        "workspaceId": clinic_id
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
