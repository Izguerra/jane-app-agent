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
import re

def validate_room_name(name: str) -> bool:
    """
    Validate room name to prevent injection attacks.
    Only allows alphanumeric, dashes, and underscores (no quotes, spaces, etc).
    """
    if not name:
        return False
    # Allow only alphanumeric, dash, and underscore. Max length 128.
    return bool(re.match(r'^[a-zA-Z0-9\-\_]{1,128}$', name))

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
        if agent_id:
            # CRITICAL FIX: Include mode AND a UUID suffix in room name to prevent stale metadata
            # from a prior session colliding with a fast reconnect
            room_name = f"agent-session-{agent_id[:8]}-{mode}-{str(uuid.uuid4())[:4]}"
        else:
            room_name = f"room-{str(uuid.uuid4())[:8]}-{mode}"

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
    target_agent_name = "supaagent-avatar-v2.1" if mode == "avatar" else "supaagent-voice-v2.1"
    
    print(f"DEBUG: [VOICE_TOKEN] Mode: {mode}, Target Agent: {target_agent_name}, Room: {room_name}")
    
    # Since explicit dispatch is implemented below, we don't need agents in room_config
    # Doing both causes duplicate agents (echo/two agents speaking)
    room_config = api.RoomConfiguration()
    # --- Resolve Settings ---
    # 1. Start with DB settings from the Workspace
    settings = get_settings(workspace.id).copy()
    
    # 1.5. Merge Integration Settings (Anam/Tavus)
    from backend.database.models.workspace import Integration
    integrations = db.query(Integration).filter(Integration.workspace_id == workspace.id, Integration.is_active == True).all()
    for integration in integrations:
        if integration.provider in ["anam", "tavus"]:
            # Merge settings if they exist
            if integration.settings:
                try:
                    int_settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
                    # Prefix keys if needed or merge directly if they follow the naming convention
                    # For Anam/Tavus we usually want them direct
                    settings.update(int_settings)
                    # Normalize keys
                    if integration.provider == "anam" and int_settings.get("persona_id"):
                        settings["anam_persona_id"] = int_settings["persona_id"]
                    if integration.provider == "tavus" and int_settings.get("replica_id"):
                        settings["tavus_replica_id"] = int_settings["replica_id"]
                except Exception as e:
                    print(f"DEBUG: Failed to parse {integration.provider} settings: {e}")

    # 2. Add DB settings from the specific Agent
    if agent_id:
        settings["agent_id"] = agent_id
        from backend.models_db import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace.id).first()
        if agent:
            base_fields = ["name", "voice_id", "language", "prompt_template", "welcome_message"]
            for field in base_fields:
                val = getattr(agent, field)
                if val is not None: settings[field] = val
            if agent.settings: settings.update(agent.settings)
        
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
    # CRITICAL: Inject the actual agent_id from the request into metadata
    # Without this, the voice/avatar worker resolves to the orchestrator agent
    # which may have no skills enabled, causing tool loading to fail.
    if agent_id:
        settings["agent_id"] = agent_id
        print(f"DEBUG: Injected agent_id={agent_id} into room metadata")
    
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

    # Create Room and explicitly dispatch agent
    try:
        print(f"DEBUG: [VOICE_TOKEN] Attempting to create room '{room_name}' and dispatch agent '{target_agent_name}'")
        lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
        room = await lkapi.room.create_room(api.CreateRoomRequest(
            name=room_name,
            empty_timeout=60,
            max_participants=5 if mode == "avatar" else 3,
            metadata=json.dumps(settings)
        ))
        print(f"DEBUG: [VOICE_TOKEN] Room creation response: {room.name if room else 'None'}")
        
        # EXPLICIT DISPATCH: Most reliable method per LiveKit docs
        # This directly tells LiveKit to send the agent to the room
        try:
            dispatch = await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name=target_agent_name,
                    metadata=json.dumps(settings)
                )
            )
            print(f"DEBUG: [VOICE_TOKEN] Agent dispatched explicitly: {dispatch}")
        except Exception as de:
            print(f"DEBUG: [VOICE_TOKEN] Explicit dispatch warning (room_config will handle): {de}")
        
        await lkapi.aclose()
    except Exception as e:
        print(f"DEBUG: [VOICE_TOKEN] Room creation warning: {e}")
        import traceback
        traceback.print_exc()
        
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


class CleanupRoomRequest(BaseModel):
    agent_id: str

@router.post("/cleanup-room")
async def cleanup_room(
    request: CleanupRoomRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Explicitly delete old LiveKit rooms for this agent before creating new ones.
    This is the core of the 'Clean Break' approach — ensures no stale rooms
    or ghost agents interfere when switching between voice and avatar modes.
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        raise HTTPException(status_code=503, detail="LiveKit not configured")

    agent_prefix = request.agent_id[:8] if request.agent_id else "unknown"
    deleted_rooms = []

    try:
        lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
        for suffix in ["-voice", "-avatar"]:
            room_name = f"agent-session-{agent_prefix}{suffix}"
            try:
                await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
                deleted_rooms.append(room_name)
                print(f"DEBUG: [CLEANUP] Deleted room: {room_name}")
            except Exception as e:
                # Room may not exist — this is fine
                print(f"DEBUG: [CLEANUP] Room {room_name} not found or already deleted: {e}")
        await lkapi.aclose()
    except Exception as e:
        print(f"ERROR: [CLEANUP] Failed to cleanup rooms: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

    return {"status": "ok", "deleted": deleted_rooms}


@router.get("/room-status")
async def room_status(
    agent_id: str,
    mode: str = "voice",
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Check whether a LiveKit room exists for the given agent and mode.
    Used by the frontend to poll and confirm that a room has been torn down
    before switching to a new mode.
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        raise HTTPException(status_code=503, detail="LiveKit not configured")

    agent_prefix = agent_id[:8] if agent_id else "unknown"
    room_name = f"agent-session-{agent_prefix}-{mode}"

    try:
        lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
        exists = len(rooms.rooms) > 0
        await lkapi.aclose()
    except Exception as e:
        print(f"DEBUG: [ROOM-STATUS] Error checking room: {e}")
        exists = False

    return {"exists": exists, "room_name": room_name}

@router.post("/outbound-twiml")
async def outbound_twiml(room: str, metadata: str = None):
    """
    TwiML endpoint for outbound calls.
    Routes call through Asterisk SIP bridge to LiveKit (same as inbound calls).
    """
    # STRICT VALIDATION: Block room names with quotes, equals, or other injection characters
    if not validate_room_name(room):
        print(f"SECURITY ALERT: Rejected malformed room name in outbound-twiml: {room}")
        # Return generic error TwiML instead of 400 to avoid revealing too much to scanners
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Invalid session.</Say></Response>',
            media_type="application/xml"
        )

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
