from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, SessionLocal
from backend.models_db import Integration, Workspace, Communication
from backend.services import get_agent_manager
from backend.services.instagram_service import InstagramService
from backend.services.conversation_history import ConversationHistoryService
from backend.security import decrypt_text
import logging
import json
import os
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/webhooks/instagram", tags=["instagram"])
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "jane_agent_verify_token")

@router.get("")
async def verify_webhook(request: Request):
    """
    Verification endpoint for Meta Webhooks.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Instagram webhook verified!")
            return Response(content=challenge, media_type="text/plain")
        else:
            logger.warning("Instagram webhook verification failed.")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    return Response(content="Instagram Webhook Endpoint", media_type="text/plain")

@router.post("")
async def instagram_webhook(request: Request):
    """
    Handle incoming Instagram messages.
    """
    try:
        body = await request.json()
        logger.info(f"Received Instagram webhook: {json.dumps(body)}")
        
        if body.get("object") == "instagram":
            for entry in body.get("entry", []):
                # The 'id' in the entry is the Instagram Business Account ID
                instagram_account_id = entry.get("id")
                
                # Combine messaging and standby events
                events = entry.get("messaging", []) + entry.get("standby", [])
                
                for messaging_event in events:
                    sender_id = messaging_event.get("sender", {}).get("id")
                    recipient_id = messaging_event.get("recipient", {}).get("id")
                    message = messaging_event.get("message", {})
                    
                    if "text" in message:
                        message_text = message["text"]
                        # Log if it's a standby event for debugging
                        is_standby = messaging_event in entry.get("standby", [])
                        event_type = "STANDBY" if is_standby else "PRIMARY"
                        logger.info(f"Received {event_type} message from {sender_id}: {message_text}")
                        
                        await process_instagram_message(instagram_account_id, sender_id, message_text)
                        
        return Response(content="EVENT_RECEIVED", media_type="text/plain")
            
    except Exception as e:
        logger.error(f"Error processing Instagram webhook: {e}")
        # Return 200 OK to prevent Meta from retrying indefinitely
        return Response(content="ERROR", media_type="text/plain")

async def process_instagram_message(instagram_account_id: str, sender_id: str, message_text: str):
    """
    Process the message with the AI agent.
    """
    db = SessionLocal()
    try:
        # Find the workspace associated with this Instagram account
        # We look for an integration that has this instagram_account_id in its settings
        # Note: In a real app with many integrations, this query should be optimized (e.g. JSONB query)
        integrations = db.query(Integration).filter(
            Integration.provider == "instagram",
            Integration.is_active == True
        ).all()
        
        workspace_id = None
        access_token = None
        
        for integration in integrations:
            try:
                settings = json.loads(integration.settings) if integration.settings else {}
                if settings.get("instagram_account_id") == instagram_account_id:
                    workspace_id = integration.workspace_id
                    
                    # 1. Try to get token from encrypted credentials (SECURE WAY)
                    if integration.credentials:
                        try:
                            decrypted = decrypt_text(integration.credentials)
                            creds = json.loads(decrypted)
                            access_token = creds.get("access_token")
                        except Exception as e:
                            logger.error(f"Failed to decrypt credentials for integration {integration.id}: {e}")
                    
                    # 2. Fallback to settings (LEGACY WAY)
                    if not access_token:
                        access_token = settings.get("access_token")
                        
                    break
            except Exception as e:
                logger.error(f"Error parsing integration settings: {e}")
                continue
        
        if not workspace_id or not access_token:
            logger.warning(f"No integration found for Instagram Account ID {instagram_account_id}")
            return

        # Ensure active Chat Session exists for history tracking
        try:
             cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
             
             # Resolve Agent ID
             agent_id = None
             if workspace_id:
                 from backend.models_db import Agent
                 default_agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
                 if default_agent:
                     agent_id = default_agent.id
             
             chat_session = db.query(Communication).filter(
                 Communication.workspace_id == workspace_id,
                 Communication.user_identifier == sender_id,
                 Communication.channel == "instagram",
                 Communication.type == "chat",
                 Communication.started_at > cutoff
             ).order_by(Communication.started_at.desc()).first()

             if not chat_session:
                 chat_session = Communication(
                     workspace_id=workspace_id,
                     user_identifier=sender_id,
                     channel="instagram",
                     type="chat",
                     direction="inbound", 
                     status="ongoing",
                     transcript="",
                     agent_id=agent_id # Link to Agent
                 )
                 db.add(chat_session)
                 db.commit()
             else:
                 # Ensure agent_id is linked
                 if not chat_session.agent_id and agent_id:
                     chat_session.agent_id = agent_id
                 pass # fix
                 db.commit()
        except Exception as e:
            logger.error(f"Failed to manage chat session: {e}", exc_info=True)

        # Get conversation history
        # Get conversation history
        history = ConversationHistoryService.get_recent_history(
            workspace_id=workspace_id,
            user_identifier=sender_id,
            channel="instagram",
            limit=10
        )
        
        # Add user message to history
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=sender_id,
            channel="instagram",
            role="user",
            content=message_text
        )
        
        # Sync to Vector DB
        from backend.services.vector_sync import sync_chat_message
        sync_chat_message(
            workspace_id=workspace_id,
            user_identifier=sender_id,
            channel="instagram",
            role="user",
            content=message_text
        )
        
        # Get AI response
        agent_manager = get_agent_manager()
        # We need team_id. Let's get it from workspace
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        team_id = workspace.team_id if workspace else 1
        
        ai_response = await agent_manager.chat(
            message_text,
            team_id=team_id,
            workspace_id=workspace_id,
            history=history
        )
        
        # Store AI response
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=sender_id,
            channel="instagram",
            role="assistant",
            content=str(ai_response)
        )
        
        # Sync to Vector DB
        sync_chat_message(
            workspace_id=workspace_id,
            user_identifier=sender_id,
            channel="instagram",
            role="assistant",
            content=str(ai_response)
        )
        
        # Send reply via Instagram Graph API
        InstagramService.send_message(access_token, sender_id, str(ai_response))
        
    except Exception as e:
        logger.error(f"Error in process_instagram_message: {e}")
    finally:
        db.close()
