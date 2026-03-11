from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database import get_db, generate_comm_id
from backend.models_db import Appointment, Workspace, Customer
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.services.calendar_service import CalendarService

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    customer_id: Optional[str] = None
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    title: str
    description: Optional[str] = None
    appointment_date: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "confirmed"


class AppointmentUpdate(BaseModel):
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


def get_current_workspace_for_appointment(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("")
def get_appointments(
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(50, le=100),
    offset: int = 0,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all appointments for the workspace"""
    workspace_id = get_workspace_context(db, user)
    
    query = db.query(Appointment).filter(Appointment.workspace_id == workspace_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    if customer_id:
        query = query.filter(Appointment.customer_id == customer_id)
    
    total = query.count()
    items = query.order_by(desc(Appointment.appointment_date)).offset(offset).limit(limit).all()
    
    # Calculate stats
    now = datetime.now()
    seven_days_later = now + timedelta(days=7)
    
    upcoming_7_days = db.query(Appointment).filter(
        Appointment.workspace_id == workspace_id,
        Appointment.appointment_date >= now,
        Appointment.appointment_date <= seven_days_later,
        Appointment.status != 'cancelled'
    ).count()
    
    completed_count = db.query(Appointment).filter(
        Appointment.workspace_id == workspace_id,
        Appointment.status == 'completed'
    ).count()
    
    # Avoid division by zero
    total_for_rate = total
    completion_rate = int((completed_count / total_for_rate * 100)) if total_for_rate > 0 else 0

    # Convert to dict
    results = [{c.name: getattr(item, c.name) for c in item.__table__.columns} for item in items]
    
    return {
        "total": total,
        "upcoming_7_days": upcoming_7_days,
        "completion_rate": completion_rate,
        "items": results,
        "page": (offset // limit) + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": offset + limit < total,
        "has_prev": offset > 0
    }


@router.post("/")
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db), 
    workspace=Depends(get_current_workspace_for_appointment)
):
    """Create a new appointment"""
    logger.info(f"Creating appointment. Incoming Status: {appointment.status}")
    # Verify customer exists and belongs to workspace
    customer = None
    if appointment.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == appointment.customer_id,
            Customer.workspace_id == workspace.id
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    # If no customer_id provided, look up by email/phone or create one
    if not customer and (appointment.customer_email or appointment.customer_phone):
        query = db.query(Customer).filter(Customer.workspace_id == workspace.id)
        if appointment.customer_email:
            query = query.filter(Customer.email == appointment.customer_email)
        elif appointment.customer_phone:
            query = query.filter(Customer.phone == appointment.customer_phone)
            
        customer = query.first()
        
        # If still not found, create a new customer
        if not customer:
            customer = Customer(
                id=generate_comm_id(),
                workspace_id=workspace.id,
                first_name=appointment.customer_first_name,
                last_name=appointment.customer_last_name,
                email=appointment.customer_email,
                phone=appointment.customer_phone,
                status="active",
                customer_type="b2c"
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            
    # If we have a customer, link it
    customer_id = customer.id if customer else None
    
    # Calendar Integration: Check availability and create event
    calendar_event_id = None
    try:
        service = CalendarService(db)
        
        # Calculate end time
        start_time = appointment.appointment_date
        end_time = start_time + timedelta(minutes=appointment.duration_minutes)
        
        logger.info(f"Attempting to create calendar event: {appointment.title} ({start_time} - {end_time})")
        
        # Prepare attendees list
        attendees = []
        if appointment.customer_email:
            attendees.append(appointment.customer_email)
            
        # Create event (this checks availability/double-booking internally)
        event_result = service.create_event(
            workspace_id=workspace.id,
            title=appointment.title,
            start_time=start_time,
            end_time=end_time,
            description=appointment.notes or "",
            attendees=attendees
        )
        
        calendar_event_id = event_result.get('id')
        logger.info(f"Calendar event created: {calendar_event_id}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Calendar Sync Error: {error_msg}")
        
        # Handle Double Booking specifically
        if "Double Booking" in error_msg:
            # Re-raise as 409
            logger.info("Raising 409 Conflict")
            raise HTTPException(status_code=409, detail=error_msg)
            
        # Ignore "No active calendar integration" error, proceed with local appointment
        if "No active calendar integration" in error_msg:
             logger.warning("No calendar integration, skipping sync.")
        else:
            # For other errors, fail hard to avoid data inconsistency if user expects sync
            logger.error(f"Critical Calendar Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to sync with calendar: {error_msg}")

    new_appointment = Appointment(
        id=generate_comm_id(),  # Reuse ID generator
        workspace_id=workspace.id,
        customer_id=customer_id,
        calendar_event_id=calendar_event_id,
        **appointment.dict(exclude={'customer_id'})
    )
    
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    # CRM Status Update
    try:
        if new_appointment.customer_id:
             from backend.services.crm_service import CRMService
             crm_service = CRMService(db)
             crm_service.update_status_on_appointment(workspace.id, new_appointment.customer_id)
             
             # Campaign Trigger
             from backend.services.campaign_service import CampaignService
             campaign_service = CampaignService(db)
             campaign_context = {
                 "customer_id": new_appointment.customer_id,
                 "appointment_id": new_appointment.id,
                 "appointment_date": new_appointment.appointment_date.isoformat(),
                 "reference_id": new_appointment.id
             }
             campaign_service.trigger_event(workspace.id, 'appointment_booked', campaign_context)
             
    except Exception as e:
        logger.error(f"Failed to update CRM or Trigger Campaign: {e}")
    
    return {c.name: getattr(new_appointment, c.name) for c in new_appointment.__table__.columns}


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific appointment"""
    workspace_id = get_workspace_context(db, user)
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.workspace_id == workspace_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {c.name: getattr(appointment, c.name) for c in appointment.__table__.columns}


@router.patch("/{appointment_id}")
def update_appointment(
    appointment_id: str,
    appointment_update: AppointmentUpdate,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an appointment and sync with Google Calendar"""
    logger.info(f"PATCH /appointments/{appointment_id} requested by user {user.id} (Team: {user.team_id})")
    
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        logger.error(f"Workspace not found for team {user.team_id}")
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    logger.info(f"Found workspace {workspace.id} for team {user.team_id}")
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.workspace_id == workspace_id
    ).first()
    
    if not appointment:
        logger.error(f"Appointment {appointment_id} not found in workspace {workspace.id}")
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update database fields
    try:
        update_data = appointment_update.dict(exclude_unset=True)
        # Filter to only include fields that exist in the Appointment model
        valid_columns = {c.name for c in Appointment.__table__.columns}
        filtered_data = {k: v for k, v in update_data.items() if k in valid_columns}
        
        for field, value in filtered_data.items():
            setattr(appointment, field, value)
        
        db.commit()
        db.refresh(appointment)
        
        # Sync with Google Calendar if calendar_event_id exists
        if appointment.calendar_event_id:
            try:
                # FIX: Pass DB session to CalendarService
                service = CalendarService(db)
                
                # Prepare updated event data
                start_dt = appointment.appointment_date
                # Ensure duration is respected if changed
                duration = appointment.duration_minutes or 60 # Default to 60 if None
                
                if start_dt:
                    end_dt = start_dt + timedelta(minutes=duration)
                    
                    # Update the calendar event
                    service.update_event(
                        workspace_id=workspace.id,
                        event_id=appointment.calendar_event_id,
                        title=appointment.title,
                        start_time=start_dt,
                        end_time=end_dt,
                        description=appointment.description or "",
                    )
                    logger.info(f"Synced appointment {appointment.id} (Event {appointment.calendar_event_id}) to Google Calendar")
            except Exception as e:
                import traceback
                logger.error(f"Warning: Failed to sync appointment {appointment.id} with Google Calendar: {e}")
                logger.error(traceback.format_exc())
                # Don't fail the request if calendar sync fails

    except Exception as e:
        db.rollback()
        import traceback
        logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")
    
    return {c.name: getattr(appointment, c.name) for c in appointment.__table__.columns}


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an appointment"""
    workspace_id = get_workspace_context(db, user)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.workspace_id == workspace_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # --- Side Effects ---
    
    # 1. Cancel in Calendar
    if appointment.calendar_event_id:
        try:
            logger.info(f"Attempting to delete calendar event: {appointment.calendar_event_id}")
            service = CalendarService(db)
            service.delete_event(workspace.id, appointment.calendar_event_id)
            logger.info("Calendar event deleted.")
        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}")
            # Continue execution (fail-open)

    # 2. Convert date for messages
    appt_date_str = appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")
    
    # 3. SMS Notification
    if appointment.customer_phone:
        try:
            logger.info(f"Sending cancellation SMS to {appointment.customer_phone}")
            from backend.services.sms_service import send_sms
            
            first_name = appointment.customer_first_name or "Valued Customer"
            message = f"Hello {first_name}, your appointment '{appointment.title}' on {appt_date_str} has been CANCELLED."
            
            send_sms(appointment.customer_phone, message, workspace_id=workspace.id)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

    # 4. Email Notification
    if appointment.customer_email:
        try:
            logger.info(f"Sending cancellation Email to {appointment.customer_email}")
            from backend.tools.mailbox_tools import MailboxTools
            
            mailbox = MailboxTools(workspace.id)
            first_name = appointment.customer_first_name or "Valued Customer"
            
            subject = f"Appointment Cancelled: {appointment.title}"
            body = f"""Hello {first_name},

Your appointment '{appointment.title}' scheduled for {appt_date_str} has been cancelled.

If you did not request this change, please contact us immediately.

Best regards,
{workspace.name}
"""
            mailbox.send_email(
                to_email=appointment.customer_email,
                subject=subject,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to send Email: {e}")

    # --- End Side Effects ---

    db.delete(appointment)
    db.commit()
    
    return {"message": "Appointment deleted and notifications sent."}
