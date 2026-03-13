from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Team, Workspace
from pydantic import BaseModel
import stripe
import os

router = APIRouter(tags=["billing-checkout"])

class CheckoutSessionRequest(BaseModel):
    price_id: str

@router.post("/create-checkout-session")
async def create_checkout_session(req: CheckoutSessionRequest, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    workspace = db.query(Workspace).filter(Workspace.team_id == team.id).first()
    ws_part = f"/{workspace.id}" if workspace else "/ws_default"
    
    base_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
    success_url = f"{base_url}{ws_part}/dashboard/account?checkout=success"
    cancel_url = f"{base_url}{ws_part}/dashboard/account/plans?checkout=cancel"

    try:
        session = stripe.checkout.Session.create(
            customer=team.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{'price': req.price_id, 'quantity': 1}],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            billing_address_collection='auto',
        )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
