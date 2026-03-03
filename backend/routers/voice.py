from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel
import os
import json
import urllib.parse
import uuid
from livekit import api
from sqlalchemy.orm import Session
from backend.settings_store import get_settings
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.lib.translation import translate_text
from backend.database import get_db, generate_workspace_id, generate_comm_id
from backend.models_db import Workspace, Team, Communication
from backend.subscription_limits import get_plan_limits
from datetime import datetime, timezone

router = APIRouter(prefix="/voice", tags=["voice"])

from typing import Optional, Dict, Any

class TokenRequest(BaseModel):
    room_name: Optional[str] = None
    participant_name: str = "user-1"
    agent_id: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    workspace_id: Optional[str] = None
    session_id: Optional[str] = None
    mode: Optional[str] = "voice" # 'voice' or 'avatar'
    tavus_replica_id: Optional[str] = None
    tavus_persona_id: Optional[str] = None

async def _generate_token(
    room_name: str,
    participant_name: str,
    agent_id: str,
    agent_config: Optional[Dict],
    current_user: AuthUser,
    db: Session,
    workspace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    mode: str = "voice",
    tavus_replica_id: Optional[str] = None,
    tavus_persona_id: Optional[str] = None
):
    print(f"DEBUG: _generate_token called with session_id={session_id}, mode={mode}")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not room_name:
        room_name = f"room-{str(uuid.uuid4())[:8]}"

    if not api_key or not api_secret or not livekit_url:
        missing = []
        if not api_key: missing.append("LIVEKIT_API_KEY")
        if not api_secret: missing.append("LIVEKIT_API_SECRET")
        if not livekit_url: missing.append("LIVEKIT_URL")
        
        raise HTTPException(
            status_code=503,
            detail=f"LiveKit is not configured. Missing environment variables: {', '.join(missing)}"
        )

    # Get workspace correctly using the robust helper
    workspace_id = get_workspace_context(db, current_user, workspace_id)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        # This shouldn't happen with get_workspace_context but safety first
        raise HTTPException(status_code=404, detail="Workspace not found after resolution")

    # CRM Ensure Customer moved below settings resolution

    # Check limits
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    plan_name = team.plan_name if team else "Starter"
    limits = get_plan_limits(plan_name)

    usage = workspace.voice_minutes_this_month or 0
    if usage >= limits["voice_minutes"]:
         raise HTTPException(status_code=403, detail="Voice minute limit reached for your plan.")

    grant = api.VideoGrants(room_join=True, room=room_name)
    unique_identity = f"user-{str(uuid.uuid4())[:8]}"
    
    grant.can_publish = True 
    grant.can_publish_data = True
    grant.can_subscribe = True
    
    # Determine Agent Dispatch Target based on Mode
    # Bypass broken main_agent.py and route natively to the specific workers
    target_agent_name = "supaagent-avatar-agent-v2" if mode == "avatar" else "supaagent-voice-agent-v2"
    
    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name=target_agent_name)]
    )
    
    # --- Resolve Settings ---
    settings = {}
    
    # 1. Start with DB settings (if agent_id exists)
    if agent_id:
        from backend.models_db import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace.id).first()
        if agent:
            base_fields = ["name", "voice_id", "language", "prompt_template", "welcome_message"]
            for field in base_fields:
                val = getattr(agent, field)
                if val is not None: settings[field] = val
            if agent.settings: settings.update(agent.settings)
        else:
             settings = get_settings(workspace.id).copy()
    else:
        settings = get_settings(workspace.id).copy()
        
    # 2. Override with agent_config from request (Unsaved Wizard Data)
    if agent_config:
        # Merge shallowly
        settings.update(agent_config)
        print(f"DEBUG: Overriding token settings with provided agent_config (keys: {list(agent_config.keys())})")

    # 3. Handle explicit Tavus ID overrides (top-level)
    if tavus_replica_id:
        settings["tavus_replica_id"] = tavus_replica_id
    if tavus_persona_id:
        settings["tavus_persona_id"] = tavus_persona_id

    # 4. Handle separate voice for AI Avatar mode
    if mode == "avatar" and settings.get("avatar_voice_id"):
        print(f"DEBUG: Overriding voice_id with avatar_voice_id: {settings['avatar_voice_id']}")
        settings["voice_id"] = settings["avatar_voice_id"]

    # Auto-translate welcome message
    if settings.get("welcome_message") and settings.get("language"):
        settings["welcome_message"] = translate_text(settings["welcome_message"], settings["language"])

    # Metadata injection
    settings["workspace_id"] = workspace.id
    settings["user_email"] = current_user.email
    settings["mode"] = mode # Inject mode into metadata so agent knows logic
    
    # Ensure Communication Log exists
    try:
        # Create Communication record
        comm_id = generate_comm_id()
        channel_type = "video_avatar" if mode == "avatar" else "phone_call"
        
        new_comm = Communication(
            id=comm_id,
            workspace_id=workspace.id,
            type="call",
            direction="inbound", 
            status="ongoing",
            started_at=datetime.now(timezone.utc),
            user_identifier=current_user.email or participant_name,
            channel=channel_type,
            agent_id=agent_id
        )
        # Link to customer if possible
        if session_id and session_id.startswith("cust_"):
             new_comm.customer_id = session_id
        
        db.add(new_comm)
        db.commit()
        db.refresh(new_comm)
        
        settings["log_id"] = comm_id
        settings["session_id"] = comm_id 
        print(f"DEBUG: Created Communication {comm_id} for token generation ({channel_type})")
        
    except Exception as e:
        print(f"ERROR: Failed to create Communication record in token gen: {e}")
        if session_id:
            settings["session_id"] = session_id
    
    # --- ENRICHMENT ---
    try:
        from backend.services import get_agent_manager
        agent_manager = get_agent_manager()
        try:
            from backend.services.crm_service import CRMService
            crm = CRMService(db)
            identifier = settings.get("user_email") or current_user.email or participant_name
            crm.ensure_customer_from_interaction(
                workspace_id=workspace.id,
                identifier=identifier,
                channel="voice",
                name=participant_name if participant_name and "user" not in participant_name else None
            )
        except Exception as e:
            print(f"DEBUG: CRM ensure failed in voice token: {e}")
        
        temp_agent = agent_manager._create_agent(settings, workspace_id=workspace.id, team_id=current_user.team_id, tools=[])
        
        if temp_agent.instructions:
            full_system_prompt = "\n\n".join(temp_agent.instructions)
            settings["prompt_template"] = full_system_prompt
    except Exception as e:
        import traceback
        print(f"DEBUG: Failed to generate enriched prompt: {e}")
        pass

    # Create Room
    try:
        lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
        room = await lkapi.room.create_room(api.CreateRoomRequest(
            name=room_name,
            empty_timeout=60,
            max_participants=4, # Increase for User + Agent + Tavus + potential backups
            agents=[api.RoomAgentDispatch(agent_name=target_agent_name)],
            metadata=json.dumps(settings)
        ))
        await lkapi.aclose()
    except Exception as e:
        print(f"DEBUG: Room creation warning: {e}")
        
    # --- TAVUS INJECTION ---
    tavus_replica_id = settings.get("tavus_replica_id") or settings.get("tavusReplicaId")
    use_tavus_avatar = settings.get("use_tavus_avatar", False) or settings.get("useTavusAvatar", False)
    tavus_persona_id = settings.get("tavus_persona_id") or settings.get("tavusPersonaId")
    
    # [DEPRECATED] Manual Tavus creation is now handled by avatar_agent.py using livekit-plugins-tavus
    # if mode == "avatar" and tavus_replica_id:
    #     print(f"DEBUG: Triggering Tavus connection for replica {tavus_replica_id}")
    #     from backend.services.tavus_service import TavusService
    #     import asyncio
        
    #     # Create a token for Tavus
    #     tavus_identity = f"tavus-{str(uuid.uuid4())[:8]}"
    #     tavus_grant = api.VideoGrants(room_join=True, room=room_name, can_subscribe=True, can_publish=True)
    #     tavus_token = (api.AccessToken(api_key, api_secret)
    #          .with_grants(tavus_grant)
    #          .with_identity(tavus_identity)
    #          .with_name("AI Avatar")
    #          .to_jwt())
             
    #     # Call API (non-blocking if possible, but async here is fine)
    #     tavUS = TavusService() # Uses env var
    #     # Run in background to not block user token return
    #     # actually, create_conversation is synchronous requests, but fast enough.
    #     # We can fire and forget?
    #     # Ideally await it to ensure it starts.
        
    #     # NOTE: Using a system prompt for Tavus context if supported
    #     system_prompt = settings.get("prompt_template", "")[:500] # Truncate for safety
        
    #     # Ensure LiveKit URL is in WSS format for Tavus
    #     tavus_livekit_url = livekit_url
    #     if tavus_livekit_url.startswith("https://"):
    #         tavus_livekit_url = tavus_livekit_url.replace("https://", "wss://")
    #     elif tavus_livekit_url.startswith("http://"):
    #         tavus_livekit_url = tavus_livekit_url.replace("http://", "ws://")
        
    #     # We don't await the result strictly for blocking, but we call it here.
    #     resp = tavUS.create_conversation(
    #         replica_id=tavus_replica_id,
    #         livekit_url=tavus_livekit_url,
    #         token=tavus_token,
    #         system_prompt=system_prompt
    #     )
    #     if resp:
    #         print(f"DEBUG: Tavus Conversation CREATED successfully: {resp.get('conversation_id')}")
    #     else:
    #         print(f"ERROR: Tavus Conversation FAILED to create. Check TAVUS_API_KEY and replica_id.")

    token = (api.AccessToken(api_key, api_secret)
             .with_grants(grant)
             .with_identity(unique_identity)
             .with_name(participant_name)
             .with_room_config(room_config)
             .with_metadata(json.dumps(settings)))
    
    return {
        "token": token.to_jwt(),
        "url": livekit_url
    }

@router.get("/token")
async def get_token_get(
    room_name: str = None, 
    participant_name: str = "user-1",
    agent_id: str = None,
    workspace_id: str = None,
    session_id: str = None,
    mode: str = "voice", # Added
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await _generate_token(room_name, participant_name, agent_id, None, current_user, db, workspace_id, session_id, mode)

@router.post("/token")
async def get_token_post(
    request: TokenRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await _generate_token(
        request.room_name, 
        request.participant_name, 
        request.agent_id, 
        request.agent_config, 
        current_user, 
        db,
        request.workspace_id,
        request.session_id,
        request.mode,
        request.tavus_replica_id,
        request.tavus_persona_id
    )


@router.post("/outbound-twiml")
async def outbound_twiml(room: str, metadata: str = None):
    """
    TwiML endpoint for outbound calls.
    Routes call through Asterisk SIP bridge to LiveKit (same as inbound calls).
    """
    try:
        # Decode metadata
        call_metadata = {}
        if metadata:
            call_metadata = json.loads(urllib.parse.unquote(metadata))
        
        # Get Asterisk SIP configuration
        asterisk_host = os.getenv("ASTERISK_HOST", "147.182.149.234")
        asterisk_sip_user = os.getenv("ASTERISK_SIP_USER", "twilio_trunk")
        
        # Build SIP URI to route through Asterisk
        # Asterisk will handle the LiveKit connection
        # Pass room name and metadata as SIP headers
        sip_uri = f"sip:{room}@{asterisk_host}"
        
        # Use Asterisk SIP bridge (same as inbound calls)
        # This leverages the existing working Asterisk → LiveKit setup
        
        # Add X-Room-Metadata header if metadata exists
        sip_suffix = ""
        if metadata:
             # Fast API decodes the query param, so we have the JSON string
             # We need to URL encode it for the SIP URI header
             encoded_metadata = urllib.parse.quote(metadata)
             sip_suffix = f"?X-Room-Metadata={encoded_metadata}"
             
        asterisk_sip_uri = f"sip:{room}@{asterisk_host}{sip_suffix}"
        
        # Generate TwiML to dial Asterisk via SIP
        twiml = '<?xml version="1.0" encoding="UTF-8"?>'
        twiml += '<Response>'
        twiml += f'<Dial>'
        twiml += f'<Sip>{asterisk_sip_uri}</Sip>'
        twiml += '</Dial>'
        twiml += '</Response>'
        
        print(f"DEBUG: Generated Asterisk SIP TwiML for room {room}")
        print(f"DEBUG: Asterisk SIP URI: {asterisk_sip_uri}")
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"ERROR in outbound-twiml: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error TwiML
        twiml = '<?xml version="1.0" encoding="UTF-8"?>'
        twiml += '<Response><Say>An error occurred. Please try again later.</Say></Response>'
        return Response(content=twiml, media_type="application/xml")


@router.post("/status-callback")
async def status_callback(request: Request):
    """
    Webhook endpoint for Twilio call status updates
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        
        print(f"Call status update: {call_sid} - {call_status}")
        
        # TODO: Update communication record in database
        
        return {"status": "ok"}
    except Exception as e:
        print(f"ERROR in status-callback: {e}")
        return {"status": "error", "message": str(e)}
