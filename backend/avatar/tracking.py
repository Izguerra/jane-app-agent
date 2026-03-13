import logging
from datetime import datetime, timezone
from backend.database import SessionLocal, generate_comm_id
from backend.models_db import Communication, Customer

logger = logging.getLogger("avatar-agent")

def start_communication_log(workspace_id, agent_id, settings, participant_identity):
    if not workspace_id: return None
    
    try:
        db = SessionLocal()
        customer_id = None
        user_email = settings.get("user_email") or settings.get("email")
        
        if user_email:
            cust = db.query(Customer).filter(Customer.workspace_id == workspace_id, Customer.email == user_email).first()
            if cust: customer_id = cust.id

        base_identifier = customer_id if customer_id else (user_email or participant_identity or "unknown_visitor")
        final_user_identifier = f"{base_identifier}#{settings.get('session_id')}" if settings.get("session_id") else base_identifier

        log_entry = Communication(
            id=generate_comm_id(), type="call", direction="inbound", status="ongoing",
            started_at=datetime.now(timezone.utc), workspace_id=workspace_id,
            channel="avatar_call", user_identifier=final_user_identifier,
            agent_id=agent_id, customer_id=customer_id,
            metadata={"mode": "avatar", "replica_id": settings.get("tavus_replica_id")}
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        log_id = log_entry.id
        db.close()
        return log_id
    except Exception as e:
        logger.error(f"Failed to log avatar call start: {e}")
        return None

async def finalize_communication_log(log_id, transcript, avatar):
    if not log_id: return
    
    try:
        db = SessionLocal()
        log = db.query(Communication).filter(Communication.id == log_id).first()
        if log:
            log.status = "completed"
            end_time = datetime.now(timezone.utc)
            log.ended_at = end_time
            log.transcript = "\n".join(transcript) if transcript else None
            log.duration = int((end_time - log.started_at).total_seconds())
            
            if avatar and hasattr(avatar, 'conversation_id'):
                meta = dict(log.metadata or {})
                meta["tavus_conversation_id"] = avatar.conversation_id
                log.metadata = meta

            db.commit()
            
            if transcript:
                try:
                    from backend.services.analysis_service import AnalysisService
                    await AnalysisService.analyze_communication(log_id, "\n".join(transcript))
                except Exception as e:
                    logger.error(f"Analysis failed: {e}")
        db.close()
    except Exception as e:
        logger.error(f"Failed to finalize log: {e}")
