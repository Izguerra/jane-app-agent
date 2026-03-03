"""
Outbound Calling Router

Handles outbound call initiation requests.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Workspace
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.services.outbound_calling_service import outbound_calling_service
from backend.services.outbound_data_service import outbound_data_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/outbound", tags=["outbound"])


class OutboundCallRequest(BaseModel):
    to_phone: str
    from_phone: Optional[str] = None
    call_intent: str = "general"
    customer_id: Optional[str] = None
    appointment_id: Optional[str] = None
    deal_id: Optional[str] = None
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    agent_id: Optional[str] = None


@router.post("/call")
async def initiate_outbound_call(
    request: OutboundCallRequest,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate an outbound call
    
    This endpoint:
    1. Validates the request
    2. Builds call context based on intent (appointment/deal/customer)
    3. Initiates the call via Twilio → LiveKit
    4. Returns call details
    """
    # Get workspace for team
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Build call context based on intent
    call_context = outbound_data_service.build_call_context(
        call_intent=request.call_intent,
        workspace_id=workspace.id,
        db=db,
        appointment_id=request.appointment_id,
        deal_id=request.deal_id,
        customer_id=request.customer_id
    )
    
    # Initiate call
    try:
        result = await outbound_calling_service.initiate_call(
            workspace_id=workspace.id,
            to_phone=request.to_phone,
            from_phone=request.from_phone,
            call_intent=request.call_intent,
            call_context=call_context,
            customer_id=request.customer_id,
            campaign_id=request.campaign_id,
            campaign_name=request.campaign_name,
            agent_id=request.agent_id,
            db=db
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
