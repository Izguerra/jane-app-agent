import logging
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from backend.database import get_db, generate_comm_id
from backend.models_db import Communication, PhoneNumber, Workspace, Agent
from backend.services.conversation_history import ConversationHistoryService
from backend.services.vector_sync import sync_chat_message
from backend.services.analysis_service import AnalysisService
from backend.services.crm_service import CRMService
from backend.services.campaign_service import CampaignService
from backend.services import get_agent_manager
from backend.services.sms_service import send_sms

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Telnyx SMS"])

@router.post("/sms/webhook")
async def telnyx_sms_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Webhook for incoming SMS from Telnyx."""
    try:
        data = await request.json()
        payload = data.get("data", {}).get("payload", {})
        if payload.get("direction") != "inbound": return {"status": "ignored"}

        from_number = payload.get("from", {}).get("phone_number")
        to_number = payload.get("to", [{}])[0].get("phone_number")
        text = payload.get("text")
        
        logger.info(f"Incoming Telnyx SMS: {from_number} -> {to_number}")
        
        workspace_id = None
        phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == to_number).first()
        if phone: workspace_id = phone.workspace_id
        if not workspace_id: return {"status": "error", "message": "unassigned number"}
            
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        team_id = workspace.team_id if workspace else None

        # CRM & Campaign
        crm = CRMService(db)
        customer = crm.ensure_customer_from_interaction(workspace_id=workspace_id, identifier=from_number, channel="sms")
        if customer:
            CampaignService(db).handle_inbound_message(workspace_id=workspace_id, customer_id=customer.id)

        # Agent Resolution
        from .utils import resolve_agent_from_phone_number
        agent = resolve_agent_from_phone_number(db, to_number, workspace_id)
        agent_id = agent.id if agent else None

        # Session Management
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        chat_session = db.query(Communication).filter(
            Communication.workspace_id == workspace_id, Communication.user_identifier == from_number,
            Communication.channel == "sms", Communication.type == "chat", Communication.status == "ongoing",
            Communication.started_at > cutoff
        ).order_by(Communication.started_at.desc()).first()

        if chat_session and chat_session.started_at < (datetime.now(timezone.utc) - timedelta(minutes=10)):
            chat_session.status, chat_session.ended_at = "completed", datetime.now(timezone.utc)
            db.commit()
            chat_session = None

        if not chat_session:
            chat_session = Communication(
                id=generate_comm_id(), workspace_id=workspace_id, user_identifier=from_number,
                channel="sms", type="chat", direction="inbound", status="ongoing",
                agent_id=agent_id, customer_id=customer.id if customer else None,
                started_at=datetime.now(timezone.utc)
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        else:
            if agent_id: chat_session.agent_id = agent_id
            if customer: chat_session.customer_id = customer.id
            chat_session.started_at = datetime.now(timezone.utc)
            db.commit()

        comm_id = chat_session.id
        history = ConversationHistoryService.get_recent_history(workspace_id=workspace_id, user_identifier=from_number, channel="sms", communication_id=comm_id)
        ConversationHistoryService.add_message(workspace_id=workspace_id, user_identifier=from_number, channel="sms", role="user", content=text, communication_id=comm_id)
        
        try: sync_chat_message(workspace_id=workspace_id, user_identifier=from_number, channel="sms", role="user", content=text)
        except: pass

        ai_response = await get_agent_manager().chat(text, team_id=team_id, workspace_id=workspace_id, history=history, agent_id=agent_id, communication_id=comm_id)
        ConversationHistoryService.add_message(workspace_id=workspace_id, user_identifier=from_number, channel="sms", role="assistant", content=ai_response, communication_id=comm_id)
        
        try: sync_chat_message(workspace_id=workspace_id, user_identifier=from_number, channel="sms", role="assistant", content=ai_response)
        except: pass

        full_history = ConversationHistoryService.get_recent_history(workspace_id=workspace_id, user_identifier=from_number, channel="sms", communication_id=comm_id)
        transcript_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in full_history])
        background_tasks.add_task(AnalysisService.analyze_communication, comm_id, transcript_str)

        send_sms(to_number=from_number, message=ai_response, workspace_id=workspace_id, agent_id=agent_id)
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error in Telnyx SMS webhook: {e}")
        return {"status": "error"}
