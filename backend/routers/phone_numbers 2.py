from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from backend.database import get_db, generate_phone_id
from backend.models_db import PhoneNumber, Workspace
from backend.auth import get_current_user, AuthUser
from backend.services.twilio_service import TwilioService
from backend.services.telnyx_service import TelnyxService
import logging
import os

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])
logger = logging.getLogger(__name__)

# Pydantic models
class PhoneNumberSearch(BaseModel):
    country_code: str = "US"
    area_code: Optional[str] = None
    voice_enabled: bool = True
    sms_enabled: bool = False
    provider: str = "twilio"

class PhoneNumberPurchase(BaseModel):
    phone_number: str
    friendly_name: Optional[str] = None
    workspace_id: str
    provider: str = "twilio"

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
    provider: str = "twilio"

@router.get("/search")
async def search_numbers(
    country: str = "US",
    area_code: Optional[str] = None,
    provider: str = "twilio",
    current_user: AuthUser = Depends(get_current_user)
):
    """Search for available phone numbers"""
    try:
        if provider == "twilio":
            twilio = TwilioService()
            numbers = twilio.search_phone_numbers(
                country_code=country,
                area_code=area_code,
                voice_enabled=True
            )
            return numbers
        elif provider == "telnyx":
            telnyx = TelnyxService()
            numbers = telnyx.search_phone_numbers(
                country_code=country,
                area_code=area_code,
                features=["voice", "sms"]
            )
            return numbers
        else:
            raise ValueError(f"Unsupported provider: {provider}")
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
    
    try:
        if purchase.provider == "twilio":
            twilio = TwilioService()
            result = twilio.purchase_phone_number(
                phone_number=purchase.phone_number,
                friendly_name=purchase.friendly_name
            )
            
            db_number = PhoneNumber(
                id=generate_phone_id(),
                workspace_id=purchase.workspace_id,
                phone_number=result["phone_number"],
                friendly_name=result.get("friendly_name"),
                twilio_sid=result["sid"],
                provider="twilio",
                voice_enabled=result["capabilities"]["voice"],
                sms_enabled=result["capabilities"]["sms"],
                monthly_cost=999,
                country_code="US"
            )
        elif purchase.provider == "telnyx":
            telnyx = TelnyxService()
            result = telnyx.purchase_phone_number(
                phone_number=purchase.phone_number,
                workspace_id=purchase.workspace_id
            )
            
            db_number = PhoneNumber(
                id=generate_phone_id(),
                workspace_id=purchase.workspace_id,
                phone_number=result["phone_number"],
                friendly_name=result.get("friendly_name", purchase.phone_number),
                telnyx_id=result["id"],
                provider="telnyx",
                voice_enabled=True, # Assuming true for standard purchase
                sms_enabled=True,
                monthly_cost=200, # Telnyx is usually cheaper
                country_code="US"
            )
        else:
            raise ValueError(f"Unsupported provider: {purchase.provider}")
        
        db.add(db_number)
        
        # Link to workspace for Voice Agent lookup
        workspace.inbound_agent_phone = result["phone_number"]
        db.add(workspace)
        db.commit()
        db.refresh(db_number)
        
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

@router.delete("")
@router.delete("/{number_id}")
async def release_number(
    number_id: Optional[str] = None,
    id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Release (delete) a phone number"""
    target_id = number_id or id
    if not target_id:
        raise HTTPException(status_code=400, detail="Phone number ID is required")
        
    print(f"DEBUG: release_number received id={target_id}")
    number = db.query(PhoneNumber).filter(PhoneNumber.id == target_id).first()
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
    
    try:
        # Release from Provider
        if number.provider == "twilio" and number.twilio_sid:
            try:
                twilio = TwilioService()
                twilio.release_phone_number(number.twilio_sid)
            except Exception as e:
                logger.error(f"Failed to release number from Twilio: {e}")
                
        elif number.provider == "telnyx" and number.telnyx_id:
            try:
                import telnyx
                telnyx_api_key = os.getenv("TELNYX_API_KEY")
                if telnyx_api_key:
                    telnyx.api_key = telnyx_api_key
                    # Telnyx SDK uses PhoneNumber to delete
                    num = telnyx.PhoneNumber.retrieve(number.telnyx_id)
                    num.delete()
            except Exception as e:
                logger.error(f"Failed to release number from Telnyx: {e}")

        # Remove from DB
        db.delete(number)
        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error releasing number: {e}")
        # If Twilio fails, we might still want to delete from DB if it's gone
        raise HTTPException(status_code=400, detail=str(e))
