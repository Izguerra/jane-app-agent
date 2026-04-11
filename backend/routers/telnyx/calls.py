import logging
import json
import asyncio
import requests
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
from telnyx import Telnyx
from datetime import datetime
from backend.database import get_db, generate_comm_id
from backend.models_db import Communication, PhoneNumber
from backend.services.integration_service import IntegrationService
from .utils import log_debug

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Telnyx Calls"])

@router.post("/calls/webhook")
async def telnyx_webhook(request: Request, db: Session = Depends(get_db)):
    """Standard Telnyx Call Control Webhook."""
    try:
        data = await request.json()
        logger.info(f"TELNYX WEBHOOK RECEIVED: {json.dumps(data)}")
        payload = data.get("data", {}).get("payload", {})
        event_type = data.get("data", {}).get("event_type")
        call_id = payload.get("call_control_id")
        
        to_number, from_number = payload.get("to"), payload.get("from")
        logger.info(f"Event: {event_type}, CallID: {call_id}, To: {to_number}, From: {from_number}")
        phone = db.query(PhoneNumber).filter((PhoneNumber.phone_number == to_number) | (PhoneNumber.phone_number == from_number)).first()
        workspace_id = phone.workspace_id if phone else None
        
        telnyx_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="telnyx", env_fallback="TELNYX_API_KEY")
        
        if event_type == "call.initiated" and payload.get("direction") in ["inbound", "incoming"]:
            requests.post(f"https://api.telnyx.com/v2/calls/{call_id}/actions/answer", headers={"Authorization": f"Bearer {telnyx_key}", "Content-Type": "application/json"}, json={})
        
        elif event_type == "call.answered":
            # Skip SIP-originated legs (these are the LiveKit SIP trunk legs)
            if str(payload.get("to", "")).startswith("sip:"): return {"status": "ok"}
            
            # Resolve agent for this call
            from .utils import resolve_agent_from_phone_number
            agent = resolve_agent_from_phone_number(db, to_number, workspace_id)
            agent_id = agent.id if agent else None

            # Create or update Communication record for CRM tracking
            comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
            if not comm:
                p_rec = db.query(PhoneNumber).filter(PhoneNumber.phone_number == payload.get("to")).first()
                call_direction = "inbound" if p_rec else "outbound"
                workspace_id = p_rec.workspace_id if p_rec else workspace_id
                if call_direction == "inbound":
                    comm = Communication(
                        id=generate_comm_id(), 
                        workspace_id=workspace_id, 
                        type="call", 
                        direction="inbound", 
                        status="answered", 
                        telnyx_call_id=call_id, 
                        user_identifier=payload.get("from"), 
                        started_at=datetime.utcnow(),
                        agent_id=agent_id
                    )
                    db.add(comm)

            if comm:
                comm.status, comm.telnyx_call_id = "answered", call_id
                if not comm.agent_id and agent_id:
                    comm.agent_id = agent_id
                db.commit()
                logger.info(f"Call {call_id} answered. Communication={comm.id}, Agent={agent_id}")
            
            # NOTE: SIP routing is now handled by LiveKit's native SIP trunk.
            # Telnyx FQDN SIP Connection → LiveKit Cloud SIP → Voice Agent dispatch.
            # The old Asterisk SIP transfer was removed because Telnyx's Call Control API
            # mangles SIP URIs, causing room name mismatches. Asterisk remains available
            # for enterprise PBX integrations via direct SIP connections.
        elif event_type == "call.hangup":
            comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
            if comm:
                comm.status, comm.ended_at = "completed", datetime.utcnow()
                db.commit()
                logger.info(f"Call {call_id} marked as completed via hangup.")
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telnyx webhook error: {e}")
        return {"status": "error"}

@router.post("/texml/inbound")
async def texml_inbound(request: Request, db: Session = Depends(get_db)):
    """TeXML endpoint for inbound calls."""
    try:
        form = await request.form()
        room_name = f"inbound-{form.get('CallSid').replace(':', '-').replace('_', '-')}"
        from backend.routers.voice import outbound_twiml
        return await outbound_twiml(room=room_name)
    except: return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error.</Say></Response>', media_type="application/xml")

@router.post("/texml/outbound")
async def texml_outbound(request: Request, db: Session = Depends(get_db)):
    """TeXML endpoint for outbound calls."""
    try:
        form = await request.form()
        call_id, to_number = form.get("CallSid"), form.get("To")
        comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first() or db.query(Communication).filter(Communication.user_identifier == to_number, Communication.direction == "outbound", Communication.status == "ongoing").order_by(Communication.started_at.desc()).first()
        if not comm: return Response(content='<Response><Say>No session.</Say></Response>', media_type="application/xml")
        
        room_name = f"outbound-{str(comm.id).replace('_', '-')}"
        from backend.routers.voice import outbound_twiml
        import urllib.parse
        meta = urllib.parse.quote(json.dumps({"communication_id": comm.id, "workspace_id": comm.workspace_id, "call_intent": comm.call_intent, "customer_id": comm.customer_id, "agent_id": comm.agent_id}))
        return await outbound_twiml(room=room_name, metadata=meta)
    except: return Response(content='<Response><Say>Error.</Say></Response>', media_type="application/xml")

@router.post("/texml/status")
async def texml_status(request: Request, db: Session = Depends(get_db)):
    """Status callback for Telnyx TeXML calls."""
    try:
        form = await request.form()
        call_id, status = form.get("CallSid"), form.get("CallStatus")
        comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
        if comm:
            if status == "completed": comm.status, comm.ended_at = "completed", datetime.utcnow()
            elif status == "answered": comm.status = "answered"
            db.commit()
        return {"status": "ok"}
    except: return {"status": "error"}
