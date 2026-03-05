from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from backend.database import get_db, generate_phone_id
from backend.models_db import PhoneNumber, Workspace
from backend.auth import get_current_user, AuthUser
from backend.services.twilio_service import TwilioService
import logging

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])
logger = logging.getLogger(__name__)

# Pydantic models
class PhoneNumberSearch(BaseModel):
    country_code: str = "US"
    area_code: Optional[str] = None
    voice_enabled: bool = True
    sms_enabled: bool = False

class PhoneNumberPurchase(BaseModel):
    phone_number: str
    friendly_name: Optional[str] = None
    workspace_id: str

class PhoneNumberConfig(BaseModel):
    voice_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None

class PhoneNumberResponse(BaseModel):
    id: str
    phone_number: str
    friendly_name: Optional[str]
    country_code: Optional[str]
    voice_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool
    voice_url: Optional[str]
    whatsapp_webhook_url: Optional[str]
    monthly_cost: Optional[int]
    is_active: bool
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

@router.get("/search")
async def search_numbers(
    country: str = "US",
    area_code: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user)
):
    """Search for available phone numbers"""
    twilio = TwilioService()
    try:
        numbers = twilio.search_phone_numbers(
            country_code=country,
            area_code=area_code,
            voice_enabled=True
        )
        return numbers
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/purchase", response_model=PhoneNumberResponse)
async def purchase_number(
    purchase: PhoneNumberPurchase,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Purchase a phone number"""
    # Verify workspace access
    workspace = db.query(Workspace).filter(
        Workspace.id == purchase.workspace_id,
        Workspace.team_id == current_user.team_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=403, detail="Access to workspace denied")
    
    twilio = TwilioService()
    try:
        # Purchase from Twilio
        result = twilio.purchase_phone_number(
            phone_number=purchase.phone_number,
            friendly_name=purchase.friendly_name
        )
        
        # Save to database
        db_number = PhoneNumber(
            id=generate_phone_id(),
            workspace_id=purchase.workspace_id,
            phone_number=result["phone_number"],
            friendly_name=result.get("friendly_name"),
            twilio_sid=result["sid"],
            voice_enabled=result["capabilities"]["voice"],
            sms_enabled=result["capabilities"]["sms"],
            monthly_cost=999, # $9.99 (in cents)
            country_code="US" # Defaulting for now as Twilio result usually needs parsing for this
        )
        
        db.add(db_number)
        
        # Link to workspace for Voice Agent lookup
        workspace.inbound_agent_phone = result["phone_number"]
        db.add(workspace)
        db.commit()
        db.refresh(db_number)
        
        # Auto-configure SIP Trunk for voice
        if db_number.voice_enabled:
            # LIVEKIT_SIP_TRUNK_URL should be in env
            # Or constructed dynamically
            # For now, we'll leaving this as a placeholder to be filled by the next step
            # logic for configuring SIP
            pass
            
        return db_number
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[PhoneNumberResponse])
async def list_numbers(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """List phone numbers for a workspace"""
    if workspace_id:
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.team_id == current_user.team_id
        ).first()
    else:
        # Default to first workspace
        workspace = db.query(Workspace).filter(
            Workspace.team_id == current_user.team_id
        ).first()
    
    if not workspace:
        # If no workspace at all, return empty list or 404
        return []
        
    numbers = db.query(PhoneNumber).options(joinedload(PhoneNumber.agent)).filter(
        PhoneNumber.workspace_id == workspace.id,
        PhoneNumber.is_active == True
    ).all()
    
    # Map to response model to include agent_name
    results = []
    for n in numbers:
        n_dict = {c.name: getattr(n, c.name) for c in n.__table__.columns}
        if n.agent:
            n_dict['agent_name'] = n.agent.name
        results.append(n_dict)

    return results

@router.delete("/{number_id}")
async def release_number(
    number_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Release (delete) a phone number"""
    print(f"DEBUG: release_number received id={number_id}")
    number = db.query(PhoneNumber).filter(PhoneNumber.id == number_id).first()
    print(f"DEBUG: release_number found number={number}")
    if not number:
        raise HTTPException(status_code=404, detail="Phone number not found")
        
    # Verify owner
    workspace = db.query(Workspace).filter(
        Workspace.id == number.workspace_id,
        Workspace.team_id == current_user.team_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=403, detail="Access denied")
    
    twilio = TwilioService()
    try:
        # Release from Twilio
        if number.twilio_sid:
            try:
                twilio.release_phone_number(number.twilio_sid)
            except Exception as e:
                logger.error(f"Failed to release number from Twilio: {e}")
                # We proceed to delete from DB anyway to avoid sync issues, 
                # but we log it. Ideally we might want to alert admin.

        
        # Remove from DB (or mark inactive)
        db.delete(number)
        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error releasing number: {e}")
        # If Twilio fails, we might still want to delete from DB if it's gone
        raise HTTPException(status_code=400, detail=str(e))
