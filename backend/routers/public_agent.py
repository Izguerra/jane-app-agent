import asyncio
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Workspace, Agent
from backend.settings_store import get_settings
from backend.lib.translation import translate_text
from backend.routers.chat import ChatRequest
from backend.services import get_agent_manager

from backend.auth import get_current_user, AuthUser

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/agent-settings/{clinic_id}")
async def get_public_agent_settings(
    clinic_id: str,
    translate: bool = False,
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.id == clinic_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Fetch default agent for the workspace to get correct settings
    agent = db.query(Agent).filter(Agent.workspace_id == workspace.id).first()
    
    settings = {}
    if agent:
        print(f"DEBUG: Found Agent {agent.id} (Language: {agent.language})")
        # Base fields
        if agent.welcome_message: settings["welcome_message"] = agent.welcome_message
        if agent.language: settings["language"] = agent.language
        if agent.voice_id: settings["voice_id"] = agent.voice_id
        
        # Merge extended
        if agent.settings:
            settings.update(agent.settings)
    else:
        print(f"DEBUG: No Agent found for workspace {workspace.id}. Using default settings.")
        # Fallback to workspace settings
        settings = get_settings(workspace.id).copy()
    
    # Auto-translate welcome message if needed
    if translate and settings.get("welcome_message") and settings.get("language"):
        try:
            print(f"DEBUG: Translating greeting to {settings.get('language')}")
            settings["welcome_message"] = translate_text(
                settings["welcome_message"], 
                settings["language"]
            )
            print(f"DEBUG: Translated greeting: {settings['welcome_message']}")
        except Exception as e:
            # Fallback to original message if translation fails
            print(f"Translation failed for public settings: {e}")
            pass
        
    return {
        "welcome_message": settings.get("welcome_message") or settings.get("welcomeGreeting"),
        "language": settings.get("language"),
        "voice_id": settings.get("voice_id"),
        "use_tavus_avatar": settings.get("use_tavus_avatar") or settings.get("useTavusAvatar", False),
        "tavus_replica_id": settings.get("tavus_replica_id") or settings.get("tavusReplicaId"),
    }

@router.get("/active-agent-settings")
async def get_active_agent_settings(
    translate: bool = False,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated endpoint to get the default active agent settings for the current user's workspace.
    Moved here to avoid routing conflicts in agents.py.
    """
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Find active agent, prioritizing recently updated
    agent = db.query(Agent).filter(
        Agent.workspace_id == workspace.id,
        Agent.is_active == True
    ).order_by(Agent.updated_at.desc()).first()
    
    # If no active agent, try any agent
    if not agent:
        agent = db.query(Agent).filter(Agent.workspace_id == workspace.id).first()
        
    settings = {}
    if agent:
        # Base fields
        if agent.welcome_message: settings["welcome_message"] = agent.welcome_message
        if agent.language: settings["language"] = agent.language
        if agent.voice_id: settings["voice_id"] = agent.voice_id
        
        # Merge extended
        if agent.settings:
            settings.update(agent.settings)
    
    # Auto-translate welcome message if needed
    if translate and settings.get("welcome_message") and settings.get("language"):
        try:
            settings["welcome_message"] = translate_text(
                settings["welcome_message"], 
                settings["language"]
            )
        except Exception:
            pass
            
    return {
        "welcome_message": settings.get("welcome_message") or settings.get("welcomeGreeting"),
        "language": settings.get("language"),
        "voice_id": settings.get("voice_id"),
        "agent_id": agent.id if agent else None,
        "use_tavus_avatar": settings.get("use_tavus_avatar") or settings.get("useTavusAvatar", False),
        "tavus_replica_id": settings.get("tavus_replica_id") or settings.get("tavusReplicaId"),
    }

@router.post("/chat/{clinic_id}")
async def public_chat(
    clinic_id: str,
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent_manager=Depends(get_agent_manager),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import desc
    from backend.models_db import Communication, Team, Customer
    from backend.services.crm_service import CRMService
    from backend.services.conversation_history import ConversationHistoryService
    from backend.services.vector_sync import sync_chat_message
    from backend.database import generate_comm_id, format_session_id
    from backend.services.sentiment_analysis import analyze_sentiment

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == clinic_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check rate limits
    from backend.routers.chat import get_plan_limits
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    limits = get_plan_limits(team.plan_name if team else "Starter")
    
    if (workspace.conversations_this_month or 0) >= limits["conversations"]:
         raise HTTPException(status_code=403, detail="Conversation limit reached for this workspace.")

    # 1. CRM & Identity Resolution
    crm_service = CRMService(db)
    
    # Use provided session ID or fallback
    raw_session = request.session_id or "unknown"
    formatted_session = format_session_id(raw_session) if raw_session != "unknown" else None
    
    # Get or Create Guest Linked to Session
    customer = crm_service.get_or_create_from_identifier(
        workspace_id=workspace.id,
        identifier=formatted_session or "unknown_widget_user",
        channel="web",
        name="Guest User"
    )
    user_id_str = customer.id if customer else f"ann_{raw_session}"

    # 2. Manage Communication Session
    # Look for active session (last 4 hours)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
    active_comm = db.query(Communication).filter(
        Communication.workspace_id == workspace.id,
        Communication.user_identifier == user_id_str, # Use CRM ID (guest_...)
        Communication.channel == "web",
        Communication.status == "ongoing",
        Communication.started_at >= cutoff
    ).order_by(desc(Communication.started_at)).first()
    
    # Check for timeout (2 minutes)
    if active_comm:
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=2)
        if active_comm.started_at < timeout_threshold:
            active_comm.status = "completed"
            active_comm.ended_at = datetime.now(timezone.utc)
            db.commit()
            active_comm = None

    if not active_comm:
        active_comm = Communication(
            id=generate_comm_id(),
            type="chat",
            direction="inbound",
            status="ongoing",
            workspace_id=workspace.id,
            channel="web",
            user_identifier=user_id_str,
            customer_id=customer.id if customer else None,
            started_at=datetime.now(timezone.utc)
        )
        # Link default agent?
        active_comm.agent_id = db.query(Agent).filter(Agent.workspace_id == workspace.id).first().id
        db.add(active_comm)
        db.commit()
        db.refresh(active_comm)
    else:
        # Update last active
        active_comm.started_at = datetime.now(timezone.utc)
        if customer and not active_comm.customer_id:
            active_comm.customer_id = customer.id
        db.commit()

    comm_id = active_comm.id

    # 3. Save User Message
    ConversationHistoryService.add_message(
        workspace_id=workspace.id,
        user_identifier=user_id_str,
        channel="web",
        role="user",
        content=request.message,
        communication_id=comm_id
    )
    # Sync if needed (maybe overkill for anonymous but good for data)
    try:
        sync_chat_message(workspace.id, user_id_str, "web", "user", request.message)
    except: pass

    from fastapi.responses import StreamingResponse
    from backend.services.acknowledgement_service import generate_dynamic_acknowledgement, stream_with_followup
    
    async def stream_generator():
        # 1. Start both tasks in parallel to minimize TTFT
        ack_task = asyncio.create_task(generate_dynamic_acknowledgement(request.message))
        agent_task = asyncio.create_task(agent_manager.chat(
            request.message, 
            team_id=workspace.team_id, 
            workspace_id=workspace.id, 
            history=request.history,
            communication_id=comm_id,
            stream=True
        ))
        
        # 2. Yield the filler as soon as it's ready (ideally < 200ms for greetings)
        filler = await ack_task
        full_content = filler
        yield filler

        # 3. Get the main generator (might take a few seconds if it's slow)
        try:
            full_response_generator = await agent_task
            
            # Stream chunks with automatic timed follow-ups if agent is slow
            async for chunk in stream_with_followup(
                response_generator=full_response_generator,
                initial_ack=filler,
                followup_delay=4.0,
                second_followup_delay=8.0
            ):
                full_content += chunk
                yield chunk
                    
            # 5. Save Assistant Response
            ConversationHistoryService.add_message(
                workspace_id=workspace.id,
                user_identifier=user_id_str,
                channel="web",
                role="assistant",
                content=full_content,
                communication_id=comm_id
            )
            
            background_tasks.add_task(
                sync_chat_message,
                workspace_id=workspace.id,
                user_identifier=user_id_str,
                channel="web",
                role="assistant",
                content=full_content
            )
            
            # 6. Post-Processing (Usage) - Requires new DB session
            from backend.database import SessionLocal
            db_post = SessionLocal()
            try:
                w = db_post.query(Workspace).filter(Workspace.id == workspace.id).first()
                if w:
                    w.conversations_this_month = (w.conversations_this_month or 0) + 1
                    db_post.commit()
            except Exception as ex:
                print(f"Failed to update workspace usage: {ex}")
            finally:
                db_post.close()
                
            # 7. Trigger Logic Analysis (Background)
            try:
                 full_history = ConversationHistoryService.get_recent_history(
                     workspace_id=workspace.id,
                     user_identifier=user_id_str,
                     channel="web",
                     limit=20,
                     communication_id=comm_id
                 )
                 transcript_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in full_history])
                 
                 from backend.services.analysis_service import AnalysisService
                 background_tasks.add_task(AnalysisService.analyze_communication, comm_id, transcript_str)
            except Exception as e:
                 print(f"Failed to queue public analysis: {e}")
                 
        except Exception as e:
            print(f"Error in stream_generator: {e}")
            yield f"Error: {e}"

    return StreamingResponse(stream_generator(), media_type="text/plain")

