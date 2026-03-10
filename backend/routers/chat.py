from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from backend.models import ChatRequest, ChatResponse
from backend.services import get_agent_manager
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db, generate_comm_id
from backend.models_db import Communication, Workspace, Team
from backend.auth import get_current_user, AuthUser
from backend.subscription_limits import get_plan_limits
from backend.services.conversation_history import ConversationHistoryService
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc
from backend.services.vector_sync import sync_chat_message

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("")
async def chat(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    agent_manager=Depends(get_agent_manager),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    try:
        # Get correct workspace using agent_id if provided
        workspace = None
        if request.agent_id:
            from backend.models_db import Agent
            req_agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
            if req_agent:
                workspace = db.query(Workspace).filter(Workspace.id == req_agent.workspace_id).first()
                if workspace and workspace.team_id != current_user.team_id:
                    raise HTTPException(status_code=403, detail="Unauthorized agent access")

        if not workspace:
            workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()

        if not workspace:
             raise HTTPException(status_code=404, detail="Workspace not found")

        # 0. CRM Integration: Ensure Customer Exists & Link to Auth User
        customer = None
        try:
             from backend.services.crm_service import CRMService
             from backend.models_db import Customer
             crm_service = CRMService(db)
             
             # 1. Try finding by Auth ID
             customer = db.query(Customer).filter(
                 Customer.workspace_id == workspace.id,
                 Customer.auth_user_id == current_user.id
             ).first()
             
             # 2. Try finding by Email
             if not customer and current_user.email:
                 customer = db.query(Customer).filter(
                     Customer.workspace_id == workspace.id,
                     func.lower(Customer.email) == current_user.email.lower(),
                     Customer.status != "deleted"
                 ).first()
                 
                 if customer and not customer.auth_user_id:
                     customer.auth_user_id = current_user.id
                     db.commit()
             
             # 3. Create/Get via Service (Fallback)
             if not customer:
                 # Clean identifier: don't double prefix
                 user_id = current_user.id
                 if not user_id.startswith("usr_"):
                     user_id = f"usr_{user_id}"
                 
                 identifier = current_user.email or user_id
                 
                 customer = crm_service.get_or_create_from_identifier(
                     workspace_id=workspace.id, 
                     identifier=identifier,
                     channel="web",
                     name=current_user.name
                 )
                 # Link auth ID if newly created
                 if customer and not customer.auth_user_id:
                     customer.auth_user_id = current_user.id
                     db.commit()
                     
        except Exception as e:
             print(f"CRM Error in chat: {e}")
             # Fallback (should theoretically not happen with correct setup)
             pass

        # Check subscription limits
        team = db.query(Team).filter(Team.id == current_user.team_id).first()
        plan_name = team.plan_name if team else "Starter"
        limits = get_plan_limits(plan_name)

        if (workspace.conversations_this_month or 0) >= limits["conversations"]:
             raise HTTPException(status_code=403, detail="Conversation limit reached for your plan.")

        # UNIFIED ID LOGIC: Always use CRM Customer ID (guest_... or cust_...)
        if customer:
            user_id_str = customer.id
        else:
            # Fallback (unlikely) - use auth ID but prefixed
            user_id_str = f"usr_{current_user.id}"
        
        # If client provides specific session ID, maintain isolation
        if request.session_id:
            user_id_str = f"{user_id_str}#{request.session_id}"

        # 1. Determine Session (Communication)
        # Look for an active session from the last 4 hours
        # Look for an active session from the last 24 hours (generous window to find and close stale sessions)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        active_comm = db.query(Communication).filter(
            Communication.workspace_id == workspace.id,
            Communication.user_identifier == user_id_str,
            Communication.channel == "web",
            Communication.status == "ongoing",
            Communication.started_at >= cutoff
        ).order_by(desc(Communication.started_at)).first()
        
        # Check for 2-minute timeout
        if active_comm:
            # Since started_at is updated on every message as a "last active" timestamp in this system:
            timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=2)
            if active_comm.started_at < timeout_threshold:
                print(f"DEBUG: Session {active_comm.id} timed out (>2 mins idle). Auto-closing.")
                active_comm.status = "completed"
                active_comm.call_outcome = "Session Timeout"
                active_comm.ended_at = datetime.now(timezone.utc)
                db.commit()
                active_comm = None # Force new session creation
        
        if active_comm:
             print(f"DEBUG: Found active_comm {active_comm.id} (Cust: {active_comm.customer_id}, User: {active_comm.user_identifier})")
             
             # Robust check: Queries directly for customer_id to avoid stale object state
             fresh_customer_id = db.query(Communication.customer_id).filter(Communication.id == active_comm.id).scalar()
             
             if customer and not fresh_customer_id:
                  active_comm.customer_id = customer.id
                  db.commit()
                  
        else:
             print("DEBUG: No active_comm found")

        if not active_comm:
            # Start new session
            
            # Resolve agent_id
            resolved_agent_id = request.agent_id
            if not resolved_agent_id and agent_manager:
                 # Get default agent for workspace
                 from backend.models_db import Agent
                 default_agent = db.query(Agent).filter(Agent.workspace_id == workspace.id).first()
                 if default_agent:
                     resolved_agent_id = default_agent.id

            # INHERITANCE FIX: If customer is not resolved validly for this request, 
            # check if this user_identifier was previously linked to a customer.
            target_customer_id = customer.id if customer else None
            
            if not target_customer_id:
                # Look for the most recent communication from this user that HAS a customer_id
                previous_linked_comm = db.query(Communication).filter(
                    Communication.workspace_id == workspace.id,
                    Communication.user_identifier == user_id_str,
                    Communication.customer_id.isnot(None)
                ).order_by(desc(Communication.started_at)).first()
                
                if previous_linked_comm:
                    print(f"DEBUG: Inheriting customer identity {previous_linked_comm.customer_id} for guest {user_id_str}")
                    target_customer_id = previous_linked_comm.customer_id

            active_comm = Communication(
                id=generate_comm_id(),  # Generate NanoID
                type="chat",
                direction="inbound",
                status="ongoing",
                workspace_id=workspace.id,
                channel="web",
                user_identifier=user_id_str,
                agent_id=resolved_agent_id, # Link to agent
                customer_id=target_customer_id, # CRITICAL FIX: Link to customer (inherited or new)
                started_at=datetime.now(timezone.utc)
            )
            db.add(active_comm)
            db.commit()
            db.refresh(active_comm)
            
        comm_id = active_comm.id
        
        # Ensure agent_id is set if it was missing (e.g. reused session)
        if not active_comm.agent_id:
             resolved_agent_id = request.agent_id
             if not resolved_agent_id:
                 from backend.models_db import Agent
                 default_agent = db.query(Agent).filter(Agent.workspace_id == workspace.id).first()
                 if default_agent:
                     resolved_agent_id = default_agent.id
             
             if resolved_agent_id:
                 active_comm.agent_id = resolved_agent_id
                 db.commit()

        # 2. Save User Message & Sync (Linked to Comm ID)
        ConversationHistoryService.add_message(
            workspace_id=workspace.id,
            user_identifier=user_id_str,
            channel="web",
            role="user",
            content=request.message,
            communication_id=comm_id
        )
        background_tasks.add_task(
            sync_chat_message,
            workspace_id=workspace.id,
            user_identifier=user_id_str,
            channel="web",
            role="user",
            content=request.message
        )

        # 3. Get AI Response (Stream)
        full_response_generator = await agent_manager.chat(
            request.message, 
            team_id=current_user.team_id,
            workspace_id=workspace.id,
            history=request.history,
            agent_id=request.agent_id,
            agent_config=request.agent_config,
            communication_id=comm_id,
            db=db,
            stream=True
        )
        
        from fastapi.responses import StreamingResponse
        from backend.services.acknowledgement_service import generate_dynamic_acknowledgement, stream_with_followup
        
        async def stream_generator():
            # Generate a dynamic, context-aware acknowledgement while the agent works
            filler = await generate_dynamic_acknowledgement(request.message)
            
            full_content = filler
            yield filler

            try:
                # Stream chunks with automatic timed follow-ups if agent is slow
                async for chunk in stream_with_followup(
                    response_generator=full_response_generator,
                    initial_ack=filler,
                    followup_delay=4.0,     # First follow-up after 4 seconds
                    second_followup_delay=8.0  # Second follow-up after 8 seconds
                ):
                    full_content += chunk
                    yield chunk
                
                # After stream finishes, perform post-processing (Uses its own DB Session!)
                ConversationHistoryService.add_message(
                    workspace_id=workspace.id,
                    user_identifier=user_id_str,
                    channel="web",
                    role="assistant",
                    content=full_content,
                    communication_id=comm_id
                )
                
                # Async Sync & Analysis
                background_tasks.add_task(
                    sync_chat_message,
                    workspace_id=workspace.id,
                    user_identifier=user_id_str,
                    channel="web",
                    role="assistant",
                    content=full_content
                )
                
                # Handle Workspace usage tracking via a separate session
                from backend.database import SessionLocal
                from backend.models_db import Workspace
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

                # 6. Trigger Dynamic Analysis
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
                     
                     from backend.services.crm_service import run_session_cleanup
                     background_tasks.add_task(run_session_cleanup, workspace.id)
                except Exception as e:
                     print(f"Failed to queue background analysis: {e}")

            except Exception as e:
                import traceback
                print(f"Streaming error: {e}")
                traceback.print_exc()

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
