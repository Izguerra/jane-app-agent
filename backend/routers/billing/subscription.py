from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from backend.models_db import Team
from pydantic import BaseModel
import stripe
import os
from datetime import datetime

router = APIRouter(tags=["billing-subscription"])

class UpgradeRequest(BaseModel):
    price_id: str

@router.get("/subscription")
async def get_subscription(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    if not team: return {"plan": "Free", "status": "active"}
    
    # Simple direct check for brevity in this refactored version
    if team.stripe_subscription_id:
        try:
            sub = stripe.Subscription.retrieve(team.stripe_subscription_id)
            price = sub.items.data[0].price
            product = stripe.Product.retrieve(price.product)
            return {
                "plan": product.name, "status": sub.status,
                "amount": price.unit_amount / 100, "is_stripe": True
            }
        except: pass
    return {"plan": team.plan_name or "Free", "status": team.subscription_status or "active", "is_stripe": bool(team.stripe_customer_id)}

@router.get("/invoices")
async def get_invoices(db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    if not team or not team.stripe_customer_id: return []
    try:
        invs = stripe.Invoice.list(customer=team.stripe_customer_id, limit=5)
        return [{"id": i.id, "date": i.created, "amount": i.total/100, "status": i.status} for i in invs.data]
    except: return []

@router.post("/portal")
async def create_portal_session(request: Request, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    if not team or not team.stripe_customer_id: raise HTTPException(status_code=400)
    url = request.headers.get("referer") or os.getenv("NEXT_PUBLIC_APP_URL") + "/dashboard/account"
    session = stripe.billing_portal.Session.create(customer=team.stripe_customer_id, return_url=url)
    return {"url": session.url}

@router.post("/preview-upgrade")
async def preview_upgrade(req: UpgradeRequest, db: Session = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == user.team_id).first()
    if not team or not team.stripe_subscription_id: return {"amount_due": 0, "can_upgrade": False}
    try:
        sub = stripe.Subscription.retrieve(team.stripe_subscription_id)
        invoice = stripe.Invoice.create_preview(
            customer=team.stripe_customer_id, subscription=team.stripe_subscription_id,
            subscription_details={"items": [{"id": sub.items.data[0].id, "price": req.price_id}]}
        )
        return {"amount_due": invoice.amount_due / 100, "can_upgrade": True}
    except: return {"amount_due": 0, "can_upgrade": False}
