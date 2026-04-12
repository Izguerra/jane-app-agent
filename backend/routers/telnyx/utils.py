import os
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models_db import PhoneNumber, Agent
from typing import Optional

def log_debug(msg):
    try:
        log_file = os.path.join(os.getcwd(), "backend/debug_webhook_telnyx.log")
        with open(log_file, "a") as f:
            f.write(f"DEBUG [{datetime.now().isoformat()}]: {msg}\n")
    except Exception as e:
        print(f"FAILED TO LOG: {e}")

def resolve_agent_from_phone_number(db: Session, phone_number: str, workspace_id: str) -> Optional[Agent]:
    """
    Deterministically resolves which agent should handle a communication.
    1. Check if the phone number is explicitly assigned to an agent.
    2. Fallback to the first active agent in the workspace.
    3. Fallback to the first agent found in the workspace.
    """
    # 1. Lookup by explicit assignment
    phone_record = db.query(PhoneNumber).filter(
        PhoneNumber.phone_number == phone_number,
        PhoneNumber.workspace_id == workspace_id
    ).first()
    
    if phone_record and phone_record.agent_id:
        agent = db.query(Agent).filter(Agent.id == phone_record.agent_id).first()
        if agent:
            log_debug(f"Resolved agent {agent.id} via explicit assignment to {phone_number}")
            return agent

    # 2. Fallback to active agent
    active_agent = db.query(Agent).filter(
        Agent.workspace_id == workspace_id,
        Agent.is_active == True
    ).first()
    
    if active_agent:
        log_debug(f"Resolved agent {active_agent.id} via active fallback for workspace {workspace_id}")
        return active_agent
        
    # 3. Last resort: First agent in workspace
    any_agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
    if any_agent:
        log_debug(f"Resolved agent {any_agent.id} via last-resort fallback for workspace {workspace_id}")
        return any_agent
        
    log_debug(f"Could not resolve any agent for workspace {workspace_id}")
    return None
