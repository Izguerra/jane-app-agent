from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

from backend.database import get_db
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.services.campaign_service import CampaignService
from backend.models_db import Campaign, CampaignStep, CampaignEnrollment, Customer, Workspace

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# --- Pydantic Models ---
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str # 'event', 'manual'
    trigger_event: Optional[str] = None
    stop_on_response: Optional[bool] = True

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    stop_on_response: Optional[bool] = None

class StepCreate(BaseModel):
    type: str # 'sms', 'email', 'wait', 'call'
    config: Dict[str, Any]
    delay_minutes: Optional[int] = 0
    time_reference: Optional[str] = 'previous_step'
    step_order: Optional[int] = None

class StepResponse(BaseModel):
    id: str
    campaign_id: str
    step_order: int
    type: str
    config: Optional[Dict[str, Any]]
    delay_minutes: int
    time_reference: str
    
    class Config:
        from_attributes = True

class CampaignResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_event: Optional[str]
    is_active: bool
    status: str
    stop_on_response: bool
    created_at: Any
    steps: List[StepResponse] = []
    
    class Config:
        from_attributes = True

class EnrollmentCustomer(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        from_attributes = True

class EnrollmentResponse(BaseModel):
    id: str
    status: str
    current_step_order: int
    next_run_at: Optional[Any] = None
    created_at: Any
    customer: EnrollmentCustomer
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("", response_model=CampaignResponse)
def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    service = CampaignService(db)
    # Get workspace for user
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    new_campaign = service.create_campaign(
        workspace_id=workspace_id,
        name=campaign.name,
        description=campaign.description,
        trigger_type=campaign.trigger_type,
        trigger_event=campaign.trigger_event
    )
    
    # Handle stop_on_response update if passed (since create_campaign might not take it yet)
    if campaign.stop_on_response is not None:
        new_campaign.stop_on_response = campaign.stop_on_response
        db.commit()
        db.refresh(new_campaign)
        
    return new_campaign

@router.get("", response_model=List[CampaignResponse])
def list_campaigns(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    try:
        workspace_id = get_workspace_context(db, user)
            
        campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).all()
        return campaigns
    except Exception as e:
        import traceback
        print(f"CRITICAL API ERROR in list_campaigns: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    # TODO: Verify workspace ownership
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Ensure steps are loaded and sorted
    # SQLAlchemy relationship usually loads, but clear explicit sort is better if not adding order_by in query
    # Using 'lazy="select"' (default) means accessing campaign.steps will load them.
    # To return in Pydantic, we just need to access it or ensure model config.
    
    # Simple sort by step_order
    campaign.steps.sort(key=lambda s: s.step_order or 0)
    
    return campaign

@router.post("/{campaign_id}/steps")
def add_step(
    campaign_id: str,
    step: StepCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    service = CampaignService(db)
    new_step = service.add_step(
        campaign_id=campaign_id,
        step_type=step.type,
        config=step.config,
        delay_minutes=step.delay_minutes,
        time_reference=step.time_reference,
        step_order=step.step_order
    )
    return new_step

@router.delete("/{campaign_id}/steps/{step_id}")
def delete_step(
    campaign_id: str,
    step_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    service = CampaignService(db)
    # TODO: Validate workspace/ownership
    success = service.delete_step(campaign_id, step_id)
    if not success:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"ok": True}

class StepUpdate(BaseModel):
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    delay_minutes: Optional[int] = None
    time_reference: Optional[str] = None
    step_order: Optional[int] = None

@router.patch("/{campaign_id}/steps/{step_id}", response_model=StepResponse)
def update_step(
    campaign_id: str,
    step_id: str,
    step_update: StepUpdate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    service = CampaignService(db)
    # TODO: Validate workspace/ownership
    
    updated_step = service.update_step(
        campaign_id=campaign_id,
        step_id=step_id,
        # Pass fields
        step_type=step_update.type,
        config=step_update.config,
        delay_minutes=step_update.delay_minutes,
        time_reference=step_update.time_reference,
        step_order=step_update.step_order
    )
    
    if not updated_step:
        raise HTTPException(status_code=404, detail="Step not found")
        
    return updated_step

class EnrollmentRequest(BaseModel):
    customer_id: str

@router.post("/{campaign_id}/enroll")
def enroll_customer(
    campaign_id: str,
    req: EnrollmentRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    service = CampaignService(db)
    
    # 1. Verify Campaign exists and belongs to workspace
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # TODO: Verify workspace ownership
    
    # 2. Check if customer exists
    from backend.models_db import Customer
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # 3. Enroll
    # For manual enrollment, we might not have a reference_id (like appointment_id). 
    # Context is minimal.
    enrollment = service.enroll_customer(
        campaign_id=campaign_id,
        customer_id=req.customer_id,
        reference_id=None, # Manual enrollment has no specific trigger event reference usually
        context={}
    )
    
    if not enrollment:
         raise HTTPException(status_code=400, detail="Enrollment failed (Campaign might have no steps)")



@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    # Verify workspace ownership
    workspace_id = get_workspace_context(db, user)

    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.workspace_id == workspace_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if update_data.name is not None:
        campaign.name = update_data.name
    if update_data.description is not None:
        campaign.description = update_data.description
    if update_data.stop_on_response is not None:
        campaign.stop_on_response = update_data.stop_on_response

    # Sync status and is_active
    if update_data.status is not None:
        campaign.status = update_data.status
        # Auto-update is_active based on status
        if campaign.status == 'active':
            campaign.is_active = True
        else:
            campaign.is_active = False
    elif update_data.is_active is not None:
        # If legacy is_active passed, map to status
        campaign.is_active = update_data.is_active
        if campaign.is_active:
             # Only update status if it was not active? Or force 'active'?
             # Better to respect specific status if we had one, but simple mapping:
             campaign.status = 'active'
        else:
             # If turning off, default to paused? Or keep as is?
             # Default to paused is created typically
             if campaign.status == 'active':
                 campaign.status = 'paused'
        
    db.commit()
    db.refresh(campaign)
    return campaign

@router.delete("/{campaign_id}")
def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    # Verify workspace ownership
    workspace_id = get_workspace_context(db, user)

    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.workspace_id == workspace_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Cascade delete is handled by DB FKs usually, but explicit delete in SQLAlchemy 
    # with cascade="all, delete-orphan" on relationship helps too.
    db.delete(campaign)
    db.commit()
    
    return {"ok": True, "message": "Campaign deleted"}

@router.get("/{campaign_id}/enrollments", response_model=List[EnrollmentResponse])
def get_campaign_enrollments(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    # Verify workspace ownership
    workspace_id = get_workspace_context(db, user)

    # Verify campaign exists
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.workspace_id == workspace_id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Fetch enrollments with customer data
    enrollments = db.query(CampaignEnrollment).join(
        Customer, CampaignEnrollment.customer_id == Customer.id
    ).filter(
        CampaignEnrollment.campaign_id == campaign_id
    ).all()
    
    # SQLAlchemy relationship might handle customer loading, but explicit join ensures we have them
    # Given model definition, we might need to rely on lazy loading or eager loading
    # To be safe and fast, let's just return them. 
    # If relationship is missing in model, Pydantic might fail unless we ensure data is present.
    # Check backend/models_db.py: CampaignEnrollment does NOT have relationship("Customer") defined!
    # We must manually attach customer or update model.
    # Let's dynamically attach for Pydantic.
    
    results = []
    for enroll in enrollments:
        # Fetch customer manually if relationship is missing
        cust = db.query(Customer).filter(Customer.id == enroll.customer_id).first()
        if cust:
             # Create Pydantic obj manually or let Pydantic handle it if we attach
             # Let's construct dict to be safe since relationship is missing in DB model
             enroll_dict = {
                 "id": enroll.id,
                 "status": enroll.status,
                 "current_step_order": enroll.current_step_order,
                 "next_run_at": enroll.next_run_at,
                 "created_at": enroll.created_at,
                 "error_message": enroll.error_message,
                 "customer": cust
             }
             results.append(enroll_dict)
    
    return results
