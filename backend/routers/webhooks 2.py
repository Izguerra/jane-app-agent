from fastapi import APIRouter, Request, Form, Response, BackgroundTasks
from typing import Optional
import logging
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

@router.post("/whatsapp")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    ProfileName: Optional[str] = Form(None)
):
    """
    Webhook endpoint for incoming WhatsApp messages from Twilio.
    Multi-tenant: Routes to the correct workspace based on the To phone number.
    Twilio sends form-encoded data, not JSON.
    """
    logger.info(f"WhatsApp message received - From: {From}, To: {To}, Body: {Body}")
    
    try:
        from backend.database import SessionLocal
        from backend.models_db import Integration, Workspace
        from backend.services import get_agent_manager
        
        # Extract phone numbers (remove 'whatsapp:' prefix)
        from_number = From.replace('whatsapp:', '')
        to_number = To.replace('whatsapp:', '')
        
        db = SessionLocal()
        try:
            # Find which workspace owns this WhatsApp number
            # Check integrations table for a WhatsApp integration with this phone number
            integrations = db.query(Integration).filter(
                Integration.provider == "whatsapp",
                Integration.is_active == True
            ).all()
            
            workspace_id = None
            for integration in integrations:
                try:
                    settings = json.loads(integration.settings) if integration.settings else {}
                    # Check if this integration's phone number matches the To number
                    integration_phone = settings.get('phone', '').replace('whatsapp:', '').replace('+', '')
                    normalized_to = to_number.replace('+', '')
                    
                    if integration_phone == normalized_to or integration_phone in normalized_to or normalized_to in integration_phone:
                        workspace_id = integration.workspace_id
                        logger.info(f"Found workspace {workspace_id} for phone {to_number}")
                        break
                except Exception as e:
                    logger.error(f"Error parsing integration settings: {e}")
                    continue
            
            # Require WhatsApp integration to be configured
            if workspace_id is None:
                logger.error(f"No WhatsApp integration found for number {to_number}. Please configure WhatsApp integration in the dashboard.")
                twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Message>This WhatsApp number is not configured. Please contact support.</Message></Response>'
                return Response(content=twiml, media_type="application/xml")
            
            # Get workspace and team_id
            workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                logger.error(f"Workspace {workspace_id} not found")
                twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Message>Sorry, this number is not configured properly.</Message></Response>'
                return Response(content=twiml, media_type="application/xml")
            
            team_id = workspace.team_id
            
            # CRM: Ensure Customer Exists
            customer = None
            try:
                from backend.services.crm_service import CRMService
                # Use main db session to keep object attached
                crm = CRMService(db)
                customer = crm.ensure_customer_from_interaction(
                    workspace_id=workspace_id,
                    identifier=from_number,
                    channel="whatsapp",
                    name=ProfileName
                )
            except Exception as e:
                logger.error(f"CRM ensure failed: {e}")

            # -----------------------------------------------------
            # CAMPAIGN SYSTEM: Stop-on-Reply Check
            # -----------------------------------------------------
            if customer:
                 try:
                     from backend.services.campaign_service import CampaignService
                     # Use the same DB session
                     campaign_service = CampaignService(db)
                     campaign_service.handle_inbound_message(workspace_id=workspace_id, customer_id=customer.id)
                 except Exception as exc:
                     logger.error(f"Failed to process campaign stop-on-reply: {exc}")
            # -----------------------------------------------------

            # Create/Update Communication Session for History
            from backend.models_db import Communication
            from datetime import datetime, timezone, timedelta
            from sqlalchemy import desc
            
            # Resolve Agent ID
            agent_id = None
            if workspace_id:
                from backend.models_db import Agent
                default_agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
                if default_agent:
                    agent_id = default_agent.id
            
            # 1. Look for Active Session
            # Match logic from chat.py: strict "ongoing" status and robust timeout check
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24) # Generous lookback to catch stale ones
            
            chat_session = db.query(Communication).filter(
                Communication.workspace_id == workspace_id,
                Communication.user_identifier == from_number,
                Communication.channel == "whatsapp",
                Communication.type == "chat",
                Communication.status == "ongoing",
                Communication.started_at > cutoff
            ).order_by(Communication.started_at.desc()).first()
            
            # 2. Check for Timeout (Auto-Close)
            if chat_session:
                # Same 2-minute timeout as Web Chat
                timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=2)
                if chat_session.started_at < timeout_threshold:
                    logger.info(f"WhatsApp Session {chat_session.id} timed out (>2 mins idle). Auto-closing.")
                    chat_session.status = "completed"
                    chat_session.call_outcome = "Session Timeout"
                    chat_session.ended_at = datetime.now(timezone.utc)
                    db.commit()
                    chat_session = None # Force new session creation

            # 3. Create New Session if needed
            if not chat_session:
                from backend.database import generate_comm_id
                chat_session = Communication(
                    id=generate_comm_id(),
                    workspace_id=workspace_id,
                    user_identifier=from_number,
                    channel="whatsapp",
                    type="chat",
                    direction="inbound", 
                    status="ongoing",
                    transcript="",
                    agent_id=agent_id, # Link Default Agent
                    customer_id=customer.id if customer else None, # Link Customer
                    started_at=datetime.now(timezone.utc)
                )
                db.add(chat_session)
                db.commit()
                db.refresh(chat_session)
            else:
                # Update existing session
                # Ensure agent_id is set if missing
                if not chat_session.agent_id and agent_id:
                    chat_session.agent_id = agent_id
                
                # Ensure customer_id is linked if missing (e.g. guest converted to customer mid-chat)
                if customer and not chat_session.customer_id:
                     chat_session.customer_id = customer.id
                     
                # Update timestamp to keep session alive
                chat_session.started_at = datetime.now(timezone.utc)
                db.commit()
            
            comm_id = chat_session.id
            
        finally:
            db.close()
        
        # Get conversation history for this user
        from backend.services.conversation_history import ConversationHistoryService
        
        history = ConversationHistoryService.get_recent_history(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            limit=20,  # Last 20 messages for better context
            communication_id=comm_id # Isolate to this session? Or general history? Chatbot uses general + limit.
            # actually Chatbot passes history from frontend. Here we fetch DB.
            # Passing comm_id to get_recent_history might restrict too much if we want *past* context?
            # get_recent_history logic usually fetches by user_identifier irrespective of session if comm_id not passed.
            # Let's stick to user_identifier for context retrieval, but link NEW messages to comm_id.
        )
        
        logger.info(f"Retrieved {len(history)} messages from history for {from_number}")
        
        # Add current user message to history LINKED TO SESSION
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            role="user",
            content=Body,
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
                content=Body
            )
        except Exception as e:
            logger.error(f"Failed to sync user message to vector DB: {e}")
        
        # Get AI response with conversation history
        agent_manager = get_agent_manager()
        ai_response = await agent_manager.chat(
            Body,
            team_id=team_id,
            workspace_id=workspace_id,
            history=history,  # Pass conversation history to maintain context
            agent_id=agent_id,
            communication_id=comm_id # Pass for tools to know context
        )
        
        logger.info(f"AI response for workspace {workspace_id}: {ai_response}")
        
        # Store AI response in history LINKED TO SESSION
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            role="assistant",
            content=ai_response,
            communication_id=comm_id
        )
        
        # Sync to Vector DB
        try:
            sync_chat_message(
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="whatsapp",
                role="assistant",
                content=ai_response
            )
        except Exception as e:
            logger.error(f"Failed to sync assistant message to vector DB: {e}")
        
        # 6. Post-Processing (Background Analysis)
        try:
             #Construct transcript
             from backend.services.conversation_history import ConversationHistoryService
             full_history = ConversationHistoryService.get_recent_history(
                 workspace_id=workspace_id,
                 user_identifier=from_number,
                 channel="whatsapp",
                 limit=20,
                 communication_id=comm_id
             )
             transcript_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in full_history])
             
             from backend.services.analysis_service import AnalysisService
             background_tasks.add_task(AnalysisService.analyze_communication, comm_id, transcript_str)
             logger.info(f"Queued background analysis for WhatsApp session {comm_id}")
        except Exception as e:
             logger.error(f"Failed to queue WhatsApp analysis: {e}")
        
        # Return TwiML response
        ai_response_escaped = ai_response.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{ai_response_escaped}</Message></Response>'
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        import traceback
        with open("backend/debug_webhook.log", "a") as f:
            f.write(f"Error: {str(e)}\n{traceback.format_exc()}\n")
        logger.error(f"Error processing Twilio message: {e}")
        
        # Return friendly error XML manually to avoid dependency issues
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Message>Sorry, I encountered an error. Please try again later.</Message></Response>'
        return Response(content=twiml, media_type="application/xml")
