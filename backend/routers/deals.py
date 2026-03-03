from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database import get_db, generate_comm_id
from backend.models_db import Deal, Workspace, Customer
from backend.auth import get_current_user, AuthUser, get_workspace_context
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/deals", tags=["deals"])


class DealCreate(BaseModel):
    customer_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    value: Optional[int] = None  # In cents
    stage: str = "lead"
    probability: int = 50
    expected_close_date: Optional[datetime] = None
    source: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    customer_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[int] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    source: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None


@router.get("/")
def get_deals(
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(50, le=100),
    offset: int = 0,
    stage: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all deals for the workspace"""
    workspace_id = get_workspace_context(db, user)
    
    query = db.query(Deal).filter(Deal.workspace_id == workspace_id)
    
    if stage:
        query = query.filter(Deal.stage == stage)
    if customer_id:
        query = query.filter(Deal.customer_id == customer_id)
    
    total = query.count()
    items = query.order_by(desc(Deal.created_at)).offset(offset).limit(limit).all()
    
    # Convert to dict
    results = [{c.name: getattr(item, c.name) for c in item.__table__.columns} for item in items]
    
    return {
        "total": total,
        "items": results,
        "page": (offset // limit) + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": offset + limit < total,
        "has_prev": offset > 0
    }


@router.post("/")
def create_deal(
    deal: DealCreate,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new deal"""
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Verify customer exists if provided
    if deal.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == deal.customer_id,
            Customer.workspace_id == workspace.id
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    new_deal = Deal(
        id=generate_comm_id(),  # Reuse ID generator
        workspace_id=workspace.id,
        **deal.dict()
    )
    
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    
    return {c.name: getattr(new_deal, c.name) for c in new_deal.__table__.columns}


@router.get("/{deal_id}")
def get_deal(
    deal_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific deal"""
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.workspace_id == workspace_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return {c.name: getattr(deal, c.name) for c in deal.__table__.columns}


@router.patch("/{deal_id}")
def update_deal(
    deal_id: str,
    deal_update: DealUpdate,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a deal"""
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.workspace_id == workspace_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Verify customer if being updated
    if deal_update.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == deal_update.customer_id,
            Customer.workspace_id == workspace.id
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    for field, value in deal_update.dict(exclude_unset=True).items():
        setattr(deal, field, value)
    
    db.commit()
    db.refresh(deal)
    
    return {c.name: getattr(deal, c.name) for c in deal.__table__.columns}


@router.delete("/{deal_id}")
def delete_deal(
    deal_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a deal"""
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.workspace_id == workspace_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    db.delete(deal)
    db.commit()
    
    return {"message": "Deal deleted successfully"}
