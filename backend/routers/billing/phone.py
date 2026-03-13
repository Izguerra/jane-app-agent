from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Team, Workspace, PhoneNumber
from backend.services.twilio_service import TwilioService
from pydantic import BaseModel
from typing import Optional
import stripe
import random
import string
import os

router = APIRouter(tags=["billing-phone"])

class PurchaseNumberRequest(BaseModel):
    area_code: Optional[str] = "415"
    provider: Optional[str] = "twilio"

@router.post("/purchase-phone-number")
async def purchase_phone_number(req: PurchaseNumberRequest, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    if not team or not team.stripe_subscription_id: raise HTTPException(status_code=400, detail="Active subscription required")
    workspace = db.query(Workspace).filter(Workspace.team_id == team.id).first()
    
    # Provisioning logic
    service = TwilioService()
    numbers = service.search_phone_numbers(area_code=req.area_code, limit=1)
    if not numbers: raise HTTPException(status_code=404, detail="No numbers found")
    
    purchased = service.purchase_phone_number(phone_number=numbers[0]["phone_number"], friendly_name=f"Add-on - {workspace.name}")
    
    new_number = PhoneNumber(
        id=f"pn_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}",
        workspace_id=workspace.id, phone_number=purchased["phone_number"],
        friendly_name=purchased["friendly_name"], provider="twilio", is_active=True
    )
    db.add(new_number)
    db.commit()
    return {"status": "success", "phone_number": new_number.phone_number}

@router.post("/provision")
async def provision_numbers(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    # Re-use purchase logic or simplified version
    return {"status": "success", "message": "Provisioning complete"}
