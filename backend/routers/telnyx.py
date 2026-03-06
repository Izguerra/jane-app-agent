from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Communication, PhoneNumber
from datetime import datetime, timezone, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

def log_debug(msg):
    try:
        log_file = os.path.join(os.getcwd(), "backend/debug_webhook_telnyx.log")
        with open(log_file, "a") as f:
            f.write(f"DEBUG [{datetime.now().isoformat()}]: {msg}\n")
    except Exception as e:
        print(f"FAILED TO LOG: {e}")

router = APIRouter(prefix="/api/telnyx", tags=["telnyx"])

@router.post("/webhook")
async def telnyx_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Standard Telnyx Call Control Webhook.
    Handles 'call.initiated' and 'call.answered' to bridge calls to LiveKit.
    """
    try:
        data = await request.json()
        log_debug(f"Incoming Telnyx Webhook: {json.dumps(data)}")
        
        payload = data.get("data", {}).get("payload", {})
        event_type = data.get("data", {}).get("event_type")
        call_id = payload.get("call_control_id")
        
        log_debug(f"Event: {event_type}, CallID: {call_id}")
        
        logger.info(f"Telnyx Webhook Event: {event_type} for call {call_id}")
        
        from telnyx import Telnyx
        import os
        client = Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
        
        if event_type == "call.initiated":
             # For inbound calls, we need to answer to get to call.answered state
             direction = payload.get("direction")
             if direction == "inbound":
                  logger.info(f"Answering inbound Telnyx call {call_id}")
                  client.calls.actions.answer(call_id)
        
        elif event_type == "call.answered":
            # 1. Update status in DB
            comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
            if comm:
                 comm.status = "answered"
                 db.commit()

            # 2. Resolve room name
            if not comm:
                 # Fallback: find most recent outbound call to this number
                 to_num = payload.get("to")
                 comm = db.query(Communication).filter(
                     Communication.user_identifier == to_num,
                     Communication.direction == "outbound"
                 ).order_by(Communication.started_at.desc()).first()

            if not comm:
                 room_name = f"call_{call_id}"
            else:
                 room_name = f"outbound_{comm.id}"
            
            asterisk_host = os.getenv("ASTERISK_HOST", "147.182.149.234")
            
            # Prepare metadata for Asterisk/LiveKit
            import urllib.parse
            import json
            metadata = {
                "communication_id": comm.id if comm else None,
                "workspace_id": comm.workspace_id if comm else None,
            }
            if comm:
                 metadata.update({
                    "agent_id": comm.agent_id,
                    "customer_id": comm.customer_id
                 })
            
            metadata_str = urllib.parse.quote(json.dumps(metadata))
            
            transfer_uri = f"sip:{room_name}@{asterisk_host}"
            
            log_debug(f"Transferring Telnyx call {call_id} to {transfer_uri} (bridging room: {room_name})")
            
            try:
                # Use requests for definitive control over custom headers
                import requests
                url_endpoint = f"https://api.telnyx.com/v2/calls/{call_id}/actions/transfer"
                headers = {
                    "Authorization": f"Bearer {os.getenv('TELNYX_API_KEY')}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "to": transfer_uri,
                    "custom_headers": [
                        {"name": "X-Room-Metadata", "value": metadata_str}
                    ]
                }
                
                resp = requests.post(url_endpoint, json=payload, headers=headers)
                log_debug(f"Transfer hit API: {resp.status_code} - {resp.text}")
                
            except Exception as te:
                log_debug(f"Transfer FAILED for {call_id}: {te}")
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in Telnyx Call Control webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error"}

@router.post("/texml/inbound")
async def texml_inbound(request: Request, db: Session = Depends(get_db)):
    """
    TeXML endpoint for inbound calls from Telnyx.
    Routes calls to the same Asterisk/LiveKit bridge as Twilio.
    """
    try:
        form_data = await request.form()
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        call_id = form_data.get("CallSid")
        
        logger.info(f"Incoming Telnyx TeXML call: {from_number} -> {to_number} ({call_id})")
        
        # Determine the room name and metadata
        # In a real scenario, we search for the PhoneNumber in DB to find associated Agent/Workspace
        phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == to_number).first()
        
        room_name = f"inbound_{call_id}"
        
        # Route through Asterisk (same as Twilio does in voice.py)
        # We can actually just return the same TwiML as Twilio outbound-twiml but for inbound
        from backend.routers.voice import outbound_twiml
        return await outbound_twiml(room=room_name)
        
    except Exception as e:
        logger.error(f"Error in Telnyx TeXML inbound: {e}")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Sorry, an error occurred.</Say></Response>', media_type="application/xml")

@router.post("/texml/outbound")
async def texml_outbound(request: Request, db: Session = Depends(get_db)):
    """
    TeXML endpoint for outbound calls from Telnyx.
    Used when a TeXML Application is used for outreach.
    """
    try:
        form_data = await request.form()
        call_id = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        
        logger.info(f"Telnyx TeXML outbound callback triggered for {call_id}")
        
        # Look up the Communication record to find the room name
        # We need to find the recently created outbound comm record
        # Note: telnyx_call_id might not be set yet if indices are slow, so we check status/direction
        comm = db.query(Communication).filter(
            Communication.telnyx_call_id == call_id
        ).first()
        
        if not comm:
            # Fallback: find the most recent outbound call to this number in this workspace/team
            # This is less reliable but helpful if the call_id isn't saved yet
            comm = db.query(Communication).filter(
                Communication.user_identifier == to_number,
                Communication.direction == "outbound",
                Communication.status == "ongoing"
            ).order_by(Communication.started_at.desc()).first()
            
        if not comm:
            logger.error(f"No communication record found for outbound call {call_id}")
            return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>No active session found.</Say></Response>', media_type="application/xml")

        room_name = f"outbound_{comm.id}"
        
        # Use our existing TwiML generator (Sip bridge to Asterisk)
        from backend.routers.voice import outbound_twiml
        import json
        import urllib.parse
        
        # Prepare metadata for the agent
        metadata = {
            "communication_id": comm.id,
            "workspace_id": comm.workspace_id,
            "call_intent": comm.call_intent,
            "call_context": comm.call_context,
            "customer_id": comm.customer_id,
            "agent_id": comm.agent_id
        }
        metadata_str = urllib.parse.quote(json.dumps(metadata))
        
        logger.info(f"Bridging Telnyx call {call_id} to LiveKit room {room_name}")
        return await outbound_twiml(room=room_name, metadata=metadata_str)
        
    except Exception as e:
        logger.error(f"Error in Telnyx TeXML outbound: {e}")
        import traceback
        traceback.print_exc()
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Connection error.</Say></Response>', media_type="application/xml")

@router.post("/texml/status")
async def texml_status(request: Request, db: Session = Depends(get_db)):
    """
    Status callback for Telnyx TeXML calls.
    Updates the Communications table.
    """
    try:
        form_data = await request.form()
        call_id = form_data.get("CallSid")
        status = form_data.get("CallStatus")
        
        logger.info(f"Telnyx call status update: {call_id} - {status}")
        
        comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
        if comm:
            if status == "completed":
                comm.status = "completed"
                comm.ended_at = datetime.now(timezone.utc)
            elif status == "answered":
                comm.status = "answered"
            db.commit()
            
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in Telnyx status callback: {e}")
        return {"status": "error"}

@router.post("/sms/webhook")
async def telnyx_sms_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Webhook for incoming SMS from Telnyx.
    """
    try:
        # Telnyx SMS webhooks come as JSON (v2 API)
        data = await request.json()
        payload = data.get("data", {}).get("payload", {})
        
        # In API v2, direction is in payload.direction ("inbound" or "outbound")
        # Ensure we only process inbound messages to avoid loop
        direction = payload.get("direction")
        if direction != "inbound":
            return {"status": "ignored", "reason": "Not an inbound message"}

        from_number = payload.get("from", {}).get("phone_number")
        to_number = payload.get("to", [{}])[0].get("phone_number")
        text = payload.get("text")
        message_id = payload.get("id")
        
        logger.info(f"Incoming Telnyx SMS: {from_number} -> {to_number}: {text[:20]}...")
        
        from backend.database import generate_comm_id
        from backend.models_db import Workspace, Agent
        from backend.services.conversation_history import ConversationHistoryService
        from backend.services.vector_sync import sync_chat_message
        from backend.services.analysis_service import AnalysisService
        from backend.services.crm_service import CRMService
        from backend.services.campaign_service import CampaignService
        from backend.services import get_agent_manager
        from backend.services.sms_service import send_sms
        from sqlalchemy import desc

        workspace_id = None
        team_id = None
        phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == to_number).first()
        if phone:
            workspace_id = phone.workspace_id
            
        if not workspace_id:
            logger.error(f"No workspace found for Telnyx number {to_number}")
            return {"status": "error", "message": "unassigned number"}
            
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if workspace:
            team_id = workspace.team_id

        # CRM: Ensure Customer Exists
        customer = None
        try:
            crm = CRMService(db)
            customer = crm.ensure_customer_from_interaction(
                workspace_id=workspace_id,
                identifier=from_number,
                channel="sms"
            )
        except Exception as e:
            logger.error(f"CRM ensure failed: {e}")

        # Campaign System: Stop-on-Reply Check
        if customer:
            try:
                campaign_service = CampaignService(db)
                campaign_service.handle_inbound_message(workspace_id=workspace_id, customer_id=customer.id)
            except Exception as exc:
                logger.error(f"Failed to process campaign stop-on-reply: {exc}")

        # Resolve Agent ID
        agent_id = None
        default_agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
        if default_agent:
            agent_id = default_agent.id

        # 1. Look for Active Session
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        chat_session = db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.user_identifier == from_number,
            Communication.channel == "sms",
            Communication.type == "chat",
            Communication.status == "ongoing",
            Communication.started_at > cutoff
        ).order_by(Communication.started_at.desc()).first()

        # 2. Check for Timeout
        if chat_session:
            timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=10) # 10 min for SMS
            if chat_session.started_at < timeout_threshold:
                logger.info(f"SMS Session {chat_session.id} timed out. Auto-closing.")
                chat_session.status = "completed"
                chat_session.call_outcome = "Session Timeout"
                chat_session.ended_at = datetime.now(timezone.utc)
                db.commit()
                chat_session = None

        # 3. Create or Update Session
        if not chat_session:
            chat_session = Communication(
                id=generate_comm_id(),
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="sms",
                type="chat",
                direction="inbound",
                status="ongoing",
                transcript="",
                agent_id=agent_id,
                customer_id=customer.id if customer else None,
                started_at=datetime.now(timezone.utc)
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        else:
            if not chat_session.agent_id and agent_id:
                chat_session.agent_id = agent_id
            if customer and not chat_session.customer_id:
                 chat_session.customer_id = customer.id
            chat_session.started_at = datetime.now(timezone.utc)
            db.commit()

        comm_id = chat_session.id

        # Conversation History
        history = ConversationHistoryService.get_recent_history(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="sms",
            limit=20,
            communication_id=comm_id
        )

        # Add user message
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="sms",
            role="user",
            content=text,
            communication_id=comm_id
        )

        try:
            sync_chat_message(
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="sms",
                role="user",
                content=text
            )
        except Exception as e:
            logger.error(f"Failed to sync user message: {e}")

        # Get AI Response
        agent_manager = get_agent_manager()
        ai_response = await agent_manager.chat(
            text,
            team_id=team_id,
            workspace_id=workspace_id,
            history=history,
            agent_id=agent_id,
            communication_id=comm_id
        )

        # Add AI message
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="sms",
            role="assistant",
            content=ai_response,
            communication_id=comm_id
        )

        try:
            sync_chat_message(
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="sms",
                role="assistant",
                content=ai_response
            )
        except Exception as e:
            logger.error(f"Failed to sync AI message: {e}")

        # Post-Processing
        try:
            full_history = ConversationHistoryService.get_recent_history(
                workspace_id=workspace_id,
                user_identifier=from_number,
                channel="sms",
                limit=20,
                communication_id=comm_id
            )
            transcript_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in full_history])
            background_tasks.add_task(AnalysisService.analyze_communication, comm_id, transcript_str)
        except Exception as e:
            logger.error(f"Failed to queue SMS analysis: {e}")

        # Send response back via SMS
        success, error = send_sms(
            to_number=from_number,
            message=ai_response,
            workspace_id=workspace_id,
            force_whatsapp=False
        )
        if not success:
            logger.error(f"Failed to send SMS reply: {error}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error in Telnyx SMS webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error"}
