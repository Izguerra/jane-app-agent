from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from backend.services.crm_service import run_session_cleanup
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.services.crm_service import CRMService
from backend.services.stripe_service import StripeService
from backend.models_db import Workspace, Communication, Appointment, Deal, ConversationMessage

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("")
def get_customers(
    page: int = 1,
    limit: int = 10,
    search: str = None,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)
        
    service = CRMService(db)
    skip = (page - 1) * limit
    return service.get_customers(workspace_id, skip=skip, limit=limit, search=search)

@router.post("")
def create_customer(
    data: dict,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    customer = service.create_customer(workspace_id, data)
    return customer

@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    customer = service.get_customer_by_id(workspace_id, customer_id)
    
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})
    
    return customer

@router.get("/{customer_id}/communications")
def get_customer_communications(
    customer_id: str,
    page: int = 1,
    limit: int = 25,
    type: str = None,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    # Trigger background expiry
    try:
        if background_tasks:
             background_tasks.add_task(run_session_cleanup, workspace_id)
    except Exception:
        pass

    # Verify customer belongs to this workspace
    service = CRMService(db)
    customer = service.get_customer_by_id(workspace_id, customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})

    # Calculate offset from page
    offset = (page - 1) * limit
    
    # Get communications with total count
    result = service.get_customer_communications(customer_id, limit=limit, offset=offset, type=type)
    
    # Return with pagination metadata
    return {
        "items": result.get("items", []),
        "total": result.get("total", 0),
        "page": page,
        "limit": limit,
        "pages": (result.get("total", 0) + limit - 1) // limit  # Ceiling division
    }

@router.get("/{customer_id}/analytics")
def get_customer_analytics(
    customer_id: str,
    period_type: str = "month",  # "month" or "year"
    period_value: str = None,  # "2025-12" or "2025", defaults to current
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customer analytics grouped by agent with time period filtering."""
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    # Verify customer belongs to this workspace
    service = CRMService(db)
    customer = service.get_customer_by_id(workspace_id, customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})

    # Get analytics data
    analytics = service.get_customer_analytics(
        customer_id=customer_id,
        workspace_id=workspace_id,
        period_type=period_type,
        period_value=period_value
    )
    
    return analytics


@router.post("/{customer_id}/analyze")
def analyze_customer(
    customer_id: str,
    data: dict,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Trigger LLM analysis for a customer interaction manually."""
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    # Check customer exists
    customer = service.get_customer_by_id(workspace_id, customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})
        
    interaction_text = data.get("text")
    interaction_type = data.get("type", "chat")
    
    if not interaction_text:
         return JSONResponse(status_code=400, content={"detail": "interaction text required"})

    result = service.analyze_and_update_customer_status(customer_id, interaction_text, interaction_type)
    return result


@router.put("/{customer_id}")
def update_customer(
    customer_id: str,
    data: dict,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    customer = service.get_customer_by_id(workspace_id, customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})

    # Update customer fields
    for key, value in data.items():
        if hasattr(customer, key) and value is not None:
            setattr(customer, key, value)
    
    db.commit()
    db.refresh(customer)
    return customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # All team members can access customer management

    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    customer = service.get_customer_by_id(workspace_id, customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})

    # SMART SOFT DELETE (As requested by User for Billing Retention)
    # 1. Cancel Future Appointments (and remove from Google Calendar)
    from backend.services.calendar_service import CalendarService
    from datetime import datetime
    
    calendar_service = CalendarService(db)
    
    appointments = db.query(Appointment).filter(Appointment.customer_id == customer_id).all()
    for appt in appointments:
        # Cancel in Google Calendar if linked
        if appt.calendar_event_id:
            try:
                print(f"DEBUG: Deleting GCal Event {appt.calendar_event_id} for appt {appt.id}")
                calendar_service.delete_event(workspace_id=workspace_id, event_id=appt.calendar_event_id)
            except Exception as e:
                print(f"ERROR: Failed to delete GCal event {appt.calendar_event_id}: {e}")
                # Continue cancellation
        
        # Mark as Cancelled in DB (retain record for billing)
        appt.status = 'cancelled'

    # 2. Soft Delete Customer (Stop Agent Interaction)
    customer.status = 'deleted'
    
    # 3. Retain Communications/Deals (Do NOT Delete - for Billing)
    
    db.commit()
    
    return {"success": True, "message": "Customer soft-deleted. History retained for billing. Future appointments cancelled."}

# Stripe Integration Endpoints

@router.post("/{customer_id}/setup-intent")
def create_setup_intent(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Create a SetupIntent for adding payment method."""
    # All team members can access customer management

    try:
        stripe_service = StripeService(db)
        setup_intent = stripe_service.create_setup_intent(customer_id)
        return {"client_secret": setup_intent.client_secret}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.post("/{customer_id}/payment-method")
def attach_payment_method(
    customer_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Attach a payment method to customer."""
    # All team members can access customer management

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            return JSONResponse(status_code=400, content={"detail": "payment_method_id required"})

        stripe_service = StripeService(db)
        payment_method = stripe_service.attach_payment_method(customer_id, payment_method_id)
        return payment_method
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.get("/{customer_id}/payment-methods")
def get_payment_methods(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customer's payment methods."""
    # All team members can access customer management

    try:
        stripe_service = StripeService(db)
        payment_methods = stripe_service.get_payment_methods(customer_id)
        return {"payment_methods": payment_methods}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.post("/{customer_id}/subscription")
def create_subscription(
    customer_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Create a subscription for customer."""
    # All team members can access customer management

    try:
        plan = data.get("plan")
        if not plan:
            return JSONResponse(status_code=400, content={"detail": "plan required"})

        stripe_service = StripeService(db)
        subscription = stripe_service.create_subscription(customer_id, plan)
        return subscription
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.put("/{customer_id}/subscription")
def update_subscription(
    customer_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Update customer's subscription plan."""
    # All team members can access customer management

    try:
        new_plan = data.get("plan")
        if not new_plan:
            return JSONResponse(status_code=400, content={"detail": "plan required"})

        stripe_service = StripeService(db)
        subscription = stripe_service.update_subscription(customer_id, new_plan)
        return subscription
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.get("/{customer_id}/proration")
def calculate_proration(
    customer_id: str,
    new_plan: str = Query(...),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Calculate proration for plan change."""
    # All team members can access customer management

    try:
        stripe_service = StripeService(db)
        proration = stripe_service.calculate_proration(customer_id, new_plan)
        return proration
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.get("/{customer_id}/invoices")
def get_invoices(
    customer_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customer's invoices."""
    # All team members can access customer management

    try:
        stripe_service = StripeService(db)
        invoices = stripe_service.get_invoices(customer_id, limit=limit)
        return {"invoices": invoices}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@router.get("/{customer_id}/appointments")
def get_customer_appointments(
    customer_id: str,
    limit: int = 10,
    page: int = 1,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customer appointments."""
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    offset = (page - 1) * limit
    return service.get_customer_appointments(customer_id, limit=limit, offset=offset)

@router.get("/{customer_id}/campaigns")
def get_customer_campaigns(
    customer_id: str,
    limit: int = 10,
    page: int = 1,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get customer campaigns."""
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)

    service = CRMService(db)
    offset = (page - 1) * limit
    return service.get_customer_campaigns(customer_id, limit=limit, offset=offset)

@router.get("/{customer_id}/voice-calls")
def get_customer_voice_calls(
    customer_id: str,
    limit: int = 20,
    page: int = 1,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Get customer voice calls."""
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, current_user, workspace_id)
        
    # Trigger background expiry
    try:
        if background_tasks:
             background_tasks.add_task(run_session_cleanup, workspace_id)
    except Exception:
        pass

    service = CRMService(db)
    offset = (page - 1) * limit
    return service.get_customer_voice_calls(customer_id, limit=limit, offset=offset)
