from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Communication, PhoneNumber
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telnyx", tags=["telnyx"])

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
async def telnyx_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook for incoming SMS from Telnyx.
    """
    try:
        # Telnyx SMS webhooks come as JSON (v2 API)
        data = await request.json()
        payload = data.get("data", {}).get("payload", {})
        
        from_number = payload.get("from", {}).get("phone_number")
        to_number = payload.get("to", [{}])[0].get("phone_number")
        text = payload.get("text")
        message_id = payload.get("id")
        
        logger.info(f"Incoming Telnyx SMS: {from_number} -> {to_number}: {text[:20]}...")
        
        # TODO: Route to Chat/SMS Agent logic
        # For now, just log to Communications table
        from backend.database import generate_comm_id
        workspace_id = None
        phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == to_number).first()
        if phone:
            workspace_id = phone.workspace_id
            
        new_comm = Communication(
            id=generate_comm_id(),
            workspace_id=workspace_id,
            type="sms",
            direction="inbound",
            status="received",
            user_identifier=from_number,
            channel="sms",
            message_content=text,
            started_at=datetime.now(timezone.utc)
        )
        db.add(new_comm)
        db.commit()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in Telnyx SMS webhook: {e}")
        return {"status": "error"}
