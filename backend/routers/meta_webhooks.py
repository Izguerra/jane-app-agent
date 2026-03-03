from fastapi import APIRouter, Request, Response, HTTPException, Depends, BackgroundTasks
import os
import json
import logging
from backend.services.meta_whatsapp_service import MetaWhatsAppService
from backend.models_db import Integration, Workspace, ConversationMessage, Communication
from backend.database import SessionLocal, get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

# Import services dynamically inside functions to avoid circular imports if needed
# requires backend.services.conversation_history

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# Load environment variables
VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
APP_SECRET = os.getenv("META_APP_SECRET")

@router.get("/meta-whatsapp")
async def verify_webhook(request: Request):
    """
    Webhook verification (Meta will call this when you configure the webhook)
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    logger.info(f"Webhook verification request: mode={mode}, token={token}")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta-whatsapp")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks = None):
    """
    Handle incoming WhatsApp messages from Meta
    """
    # 1. Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    
    if APP_SECRET and not MetaWhatsAppService.verify_webhook_signature(body, signature, APP_SECRET):
        logger.warning("Meta webhook signature invalid")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # 2. Parse payload
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.info(f"Received Meta webhook: {json.dumps(data, indent=2)}")
    
    # 3. Process entries
    # Meta sends a list of 'entry' objects
    for entry in data.get("entry", []):
        # Each entry can have multiple 'changes'
        for change in entry.get("changes", []):
            value = change.get("value", {})
            field = change.get("field")
            
            if field != "messages":
                continue
                
            # Handle incoming messages
            if "messages" in value:
                for message in value["messages"]:
                    await process_incoming_message(message, value.get("metadata", {}))
                    
                    # Trigger Background Cleanup
                    if background_tasks and value.get("metadata", {}).get("phone_number_id"):
                        # We need to resolve workspace_id properly. 
                        # process_incoming_message resolves it internally, but returns nothing.
                        # For simplicity, we can't easily pass it here without refactoring.
                        # BUT, we can just run the cleanup in process_incoming_message if we pass background_tasks down?
                        # Or, refactor process_incoming_message to return workspace_id?
                        pass 
            
            # Handle status updates (sent, delivered, read)
            if "statuses" in value:
                for status in value["statuses"]:
                    await process_message_status(status)
                    
    return {"status": "ok"}


async def process_incoming_message(message: dict, metadata: dict):
    """
    Process a single incoming message
    """
    from backend.services.agent_manager import AgentManager
    from backend.services.conversation_history import ConversationHistoryService
    from backend.agent_tools import AgentTools
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import desc
    from fastapi import BackgroundTasks # Not needed here if we rely on the router trigger but refactoring is hard inside loop.

    # ... [Rest of imports] ...
    
    phone_number_id = metadata.get("phone_number_id")
    from_number = message.get("from")
    # ...
    
    # [Inside DB try block]
    db = SessionLocal()
    try:
        # ... [Workspace Resolution] ...
        
        target_integration = None
        # ...
        
        workspace_id = target_integration.workspace_id
        
        # ... [Logic] ...
        
        # FIRE CLEANUP HERE (Synchronous inside async func? No, better to trigger async task if possible)
        # But we don't have BackgroundTasks object here easily unless passed.
        # Let's just run it "fire and forget" if possible or as part of this flow?
        # Ideally we'd use BackgroundTasks.
        # We will add it to `handle_webhook` signature and pass it down?
        # NO, `process_incoming_message` is async.
        
        # Let's just launch the cleanup task here using our helper and run_in_threadpool or just call it?
        # It's a quick DB query, calling it directly is acceptable given it's async and we want to ensure it runs.
        # Or better: `from backend.services.crm_service import run_session_cleanup`
        # `run_session_cleanup(workspace_id)`
        
        # Let's do it at the end of the success path.
        from backend.services.crm_service import run_session_cleanup
        # Run in executor to not block loop
        # executor.submit(run_session_cleanup, workspace_id) 
        # For now, just call it. It's fast enough.
        run_session_cleanup(workspace_id)
        
    except Exception as e:
        logger.error(f"Error processing Meta WhatsApp message: {e}", exc_info=True)
    finally:
        db.close()


async def process_incoming_message(message: dict, metadata: dict):
    """
    Process a single incoming message
    """
    from backend.services.agent_manager import AgentManager
    from backend.services.conversation_history import ConversationHistoryService
    from backend.agent_tools import AgentTools
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import desc
    
    phone_number_id = metadata.get("phone_number_id")
    from_number = message.get("from")
    message_type = message.get("type")
    message_id = message.get("id")
    timestamp = message.get("timestamp")
    
    logger.info(f"Processing message from {from_number} (ID: {message_id})")
    
    # Only handle text messages for now
    if message_type == "text":
        text_content = message.get("text", {}).get("body", "")
    else:
        logger.info(f"Ignoring message type: {message_type}")
        # Could send a generic "I can only process text" response here
        return

    db = SessionLocal()
    try:
        # 1. Find the integration and workspace using phone_number_id
        # We look for an integration where the settings JSON contains this phone_number_id
        # PostgreSQL specific JSON query could be efficient, but simple verify for now:
        integrations = db.query(Integration).filter(
            Integration.provider == "meta_whatsapp",
            Integration.is_active == True
        ).all()
        
        target_integration = None
        for integration in integrations:
            settings = integration.get_settings_dict()
            if settings.get("phone_number_id") == phone_number_id:
                target_integration = integration
                break
        
        if not target_integration:
            logger.error(f"No active 'meta_whatsapp' integration found for phone_number_id: {phone_number_id}")
            return

        workspace_id = target_integration.workspace_id
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        
        if not workspace:
            logger.error(f"Workspace {workspace_id} not found")
            return
            
        logger.info(f"Matched workspace: {workspace.name} (ID: {workspace_id}) for phone {phone_number_id}")

        # Resolve Agent ID
        agent_id = None
        from backend.models_db import Agent
        default_agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
        if default_agent:
            agent_id = default_agent.id

        # Resolve Customer (Real or Guest)
        from backend.services.crm_service import CRMService
        crm_service = CRMService(db)
        customer_obj = crm_service.get_or_create_from_identifier(
            workspace_id=workspace_id,
            identifier=from_number,
            channel="whatsapp",
            name=None # Meta sometimes provides name in profile, could extract if available in 'message' or 'contacts' payload
        )
        customer_id = customer_obj.id if customer_obj else None

        # Ensure active Chat Session exists for history tracking
        chat_session = None
        try:
             # Look for an active session from the last 24 hours (WhatsApp sessions are longer usually)
             # But let's keep 4 hours to match web chat consistency or 24h? WhatsApp window is 24h.
             # Let's use 4 hours for "Active Status" consistency.
             cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
             
             chat_session = db.query(Communication).filter(
                 Communication.workspace_id == workspace_id,
                 Communication.user_identifier == from_number,
                 Communication.channel == "whatsapp",
                 Communication.type == "chat",
                 Communication.status == "ongoing",
                 Communication.started_at >= cutoff
             ).order_by(desc(Communication.started_at)).first()

             if not chat_session:
                 chat_session = Communication(
                     workspace_id=workspace_id,
                     user_identifier=from_number,
                     channel="whatsapp",
                     type="chat",
                     direction="inbound", 
                     status="ongoing",
                     transcript="",
                     starts_at=datetime.now(timezone.utc),
                     agent_id=agent_id,
                     customer_id=customer_id
                 )
                 db.add(chat_session)
                 db.commit()
                 db.refresh(chat_session)
                 logger.info(f"Created new WhatsApp chat session {chat_session.id}")
             else:
                 # Update timestamp to bump to top
                 chat_session.started_at = datetime.now(timezone.utc)
                 # Ensure agent_id is linked
                 if not chat_session.agent_id and agent_id:
                     chat_session.agent_id = agent_id
                 # Ensure customer_id is linked (if it was missing before)
                 if not chat_session.customer_id and customer_id:
                     chat_session.customer_id = customer_id
                 db.commit()
                 
        except Exception as e:
            logger.error(f"Failed to manage chat session: {e}", exc_info=True)

        comm_id = chat_session.id if chat_session else None

        # 2. Start Meta Service for response
        integration_settings = target_integration.get_settings_dict()
        meta_service = MetaWhatsAppService(
            access_token=integration_settings.get("access_token"),
            phone_number_id=phone_number_id
        )

        # Mark user message as read
        meta_service.mark_as_read(message_id)

        # 3. Save User Message
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",  # or "meta_whatsapp"
            role="user",
            content=text_content,
            communication_id=comm_id
        )
        
        # Sync to Vector DB
        try:
            from backend.services.vector_sync import sync_chat_message
            sync_chat_message(
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="whatsapp",
                role="user",
                content=text_content
            )
        except Exception as e:
            logger.error(f"Failed to sync user message to vector DB: {e}")
        
        # 3.5 Start immediate dynamic acknowledgement and Agent Response in parallel
        from backend.services.acknowledgement_service import generate_dynamic_acknowledgement
        from backend.services import get_agent_manager
        
        # Construct history for the agent
        history = ConversationHistoryService.get_recent_history(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            limit=10,
            hours=24
        )
        
        ack_task = asyncio.create_task(generate_dynamic_acknowledgement(text_content))
        agent_manager = get_agent_manager()
        agent_task = asyncio.create_task(agent_manager.chat(
            message=text_content,
            team_id=workspace.team_id,
            workspace_id=workspace_id,
            history=history
        ))

        # Send filler if non-empty (fast path for greetings returns "")
        filler = await ack_task
        if filler and len(filler.strip()) > 0:
            meta_service.send_message(to=from_number, message=filler)
        
        # 4. Wait for Agent Response
        ai_response_text = await agent_task
        
        if not ai_response_text:
            ai_response_text = "I'm sorry, I couldn't process your request."

        # 5. Send AI Response
        meta_service.send_message(to=from_number, message=ai_response_text)
        
        # 6. Save AI Response
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            role="assistant",
            content=ai_response_text,
            communication_id=comm_id
        )
        
        # Sync to Vector DB
        try:
            sync_chat_message(
                 workspace_id=workspace_id,
                 user_identifier=from_number,
                 channel="whatsapp",
                 role="assistant",
                 content=ai_response_text
            )
        except Exception as e:
            logger.error(f"Failed to sync assistant message to vector DB: {e}")
        
        # 7. Update usage stats
        workspace.conversations_this_month = (workspace.conversations_this_month or 0) + 1
        
        # Update session timestamp again? No, once per turn is fine.
        if chat_session:
             chat_session.started_at = datetime.now(timezone.utc)
             
        db.commit()
        
    except Exception as e:
        logger.error(f"Error processing Meta WhatsApp message: {e}", exc_info=True)
    finally:
        db.close()


async def process_message_status(status: dict):
    """
    Handle message delivery updates (sent, delivered, read)
    """
    message_id = status.get("id")
    recipient_id = status.get("recipient_id")
    status_type = status.get("status")
    
    logger.info(f"Message status update: ID={message_id}, Status={status_type}")
    
    # Here we could update a 'message_status' table if we were tracking individual message states
    # For now, just logging is sufficient.
