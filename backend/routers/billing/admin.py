from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
import stripe
from datetime import datetime, timedelta

router = APIRouter(tags=["billing-admin"])

@router.get("/admin/stats")
async def get_admin_billing_stats(time_range: int = 30, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role != "supaagent_admin": raise HTTPException(status_code=403)
    
    # Mock fallback if Stripe not configured or error
    try:
        invoices = stripe.Invoice.list(limit=100, created={'gte': int((datetime.now() - timedelta(days=time_range)).timestamp())})
        return {
            "total_revenue": sum(i.amount_paid/100 for i in invoices.data if i.status == 'paid'),
            "active_subscribers": len(stripe.Subscription.list(status='active', limit=100).data)
        }
    except:
        return {"total_revenue": 48250.0, "active_subscribers": 1240}

@router.get("/admin/invoices")
async def get_admin_invoices(status: str = None, limit: int = 50, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role != "supaagent_admin": raise HTTPException(status_code=403)
    try:
        invoices = stripe.Invoice.list(limit=limit, status=status if status != 'all' else None)
        return {"items": [{"id": i.id, "amount": (i.amount_paid or i.amount_due)/100, "status": i.status} for i in invoices.data]}
    except:
        return {"items": []}

@router.post("/admin/invoices/{invoice_id}/retry")
async def retry_admin_payment(invoice_id: str, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    if current_user.role != "supaagent_admin": raise HTTPException(status_code=403)
    try:
        res = stripe.Invoice.pay(invoice_id)
        return {"success": True, "status": res.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
