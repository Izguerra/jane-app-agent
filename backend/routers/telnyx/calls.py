import logging
import json
import asyncio
import os
import telnyx
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db, generate_comm_id
from backend.models_db import Communication, PhoneNumber
from backend.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Telnyx Calls"])

@router.post("/calls/webhook")
async def telnyx_webhook(request: Request, db: Session = Depends(get_db)):
    """Standard Telnyx Call Control Webhook."""
    try:
        data = await request.json()
        logger.info(f"TELNYX WEBHOOK: {json.dumps(data)}")
        payload = data.get("data", {}).get("payload", {})
        event_type = data.get("data", {}).get("event_type")
        call_id = payload.get("call_control_id")
        
        to_number = payload.get("to")
        phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == to_number).first()
        workspace_id = phone.workspace_id if phone else None
        
        # Robust Key Resolution
        telnyx_key = IntegrationService.get_provider_key(workspace_id=workspace_id, provider="telnyx", env_fallback="TELNYX_API_KEY")
        if not telnyx_key:
            logger.error(f"Critical: No Telnyx API Key found for workspace {workspace_id}")
            return {"status": "error", "message": "Missing API Key"}

        telnyx.api_key = telnyx_key
        
        if event_type == "call.initiated" and payload.get("direction") in ["inbound", "incoming"]:
            # Use SDK for atomic Answer command
            try:
                call = telnyx.Call.retrieve(call_id)
                call.answer()
                logger.info(f"Answer command sent for call {call_id}")
            except Exception as e:
                logger.error(f"Failed to answer call {call_id}: {e}")
        
        elif event_type == "call.answered":
            if str(to_number).startswith("sip:"): return {"status": "ok"}
            
            from .utils import resolve_agent_from_phone_number
            agent = resolve_agent_from_phone_number(db, to_number, workspace_id)
            agent_id = agent.id if agent else None

            comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
            if not comm:
                comm = Communication(
                    id=generate_comm_id(), workspace_id=workspace_id, type="call", direction="inbound", 
                    status="answered", telnyx_call_id=call_id, user_identifier=payload.get("from"), 
                    started_at=datetime.utcnow(), agent_id=agent_id
                )
                db.add(comm)

            if comm:
                comm.status = "answered"
                if agent_id: comm.agent_id = agent_id
                db.commit()
                logger.info(f"Call {call_id} handled. Agent={agent_id}")
            
        elif event_type == "call.hangup":
            comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first()
            if comm:
                comm.status, comm.ended_at = "completed", datetime.utcnow()
                db.commit()
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telnyx webhook error: {e}")
        return {"status": "error"}

@router.post("/texml/inbound")
async def texml_inbound(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        room_name = f"inbound-{form.get('CallSid').replace(':', '-').replace('_', '-')}"
        from backend.routers.voice import outbound_twiml
        return await outbound_twiml(room=room_name)
    except: return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error.</Say></Response>', media_type="application/xml")

@router.post("/texml/outbound")
async def texml_outbound(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        call_id, to_number = form.get("CallSid"), form.get("To")
        comm = db.query(Communication).filter(Communication.telnyx_call_id == call_id).first() or \
               db.query(Communication).filter(Communication.user_identifier == to_number, Communication.direction == "outbound", Communication.status == "ongoing").order_by(Communication.started_at.desc()).first()
        if not comm: return Response(content='<Response><Say>No session.</Say></Response>', media_type="application/xml")
        from backend.routers.voice import outbound_twiml
        import urllib.parse
        meta = urllib.parse.quote(json.dumps({"communication_id": comm.id, "workspace_id": comm.workspace_id, "call_intent": comm.call_intent, "customer_id": comm.customer_id, "agent_id": comm.agent_id}))
        return await outbound_twiml(room=f"outbound-{str(comm.id).replace('_', '-')}", metadata=meta)
    except: return Response(content='<Response><Say>Error.</Say></Response>', media_type="application/xml")

@router.post("/texml/status")
async def texml_status(request: Request, db: Session = Depends(get_db)):
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
