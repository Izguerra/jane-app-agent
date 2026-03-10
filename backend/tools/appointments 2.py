import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List
from livekit.agents import llm
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import dependencies
from backend.models_db import Appointment, User, Customer, Communication
from backend.database import get_db, SessionLocal, generate_appointment_id, generate_confirmation_code
from backend.services.calendar_service import CalendarService

logger = logging.getLogger("appointment-tools")

class AppointmentTools:
    def __init__(self, workspace_id: int, customer_id: str = None, communication_id: str = None):
        self.workspace_id = workspace_id
        self.customer_id = customer_id
        self.communication_id = communication_id

    @llm.function_tool(description="Get available time slots for a specific date.")
    def get_availability(self, date: str = None) -> str:
        """
        Get available time slots for a specific date.
        Args:
           date: Date in YYYY-MM-DD format (optional, defaults to today)
        """
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
                
            db = SessionLocal()
            try:
                # Basic Availability Logic (Placeholder - would integrate with CalendarService)
                # For now, let's assume 9-5 availability with some random slots taken
                
                # Check existing appointments
                start_of_day = datetime.strptime(date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                existing = db.query(Appointment).filter(
                    Appointment.workspace_id == self.workspace_id,
                    Appointment.appointment_date >= start_of_day,
                    Appointment.appointment_date < end_of_day,
                    Appointment.status != 'cancelled'
                ).all()
                
                busy_times = [appt.appointment_date.strftime('%H:%M') for appt in existing]
                
                # Mock slots (9:00 to 17:00)
                all_slots = [
                    "09:00", "10:00", "11:00", "12:00", 
                    "13:00", "14:00", "15:00", "16:00", "17:00"
                ]
                
                available = [slot for slot in all_slots if slot not in busy_times]
                
                if not available:
                    return f"No slots available for {date}."
                
                return f"Available slots for {date}: {', '.join(available)}"
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return "Sorry, I couldn't check availability right now."

    @llm.function_tool(description="Create a new appointment.")
    def create_appointment(
        self, 
        title: str, 
        start_time: str, 
        duration_minutes: int = 60, 
        description: str = "",
        attendee_name: str = None, 
        attendee_email: str = None,
        attendee_phone: str = None
    ) -> str:
        """
        Create a new appointment.
        Args:
            title: Title of the appointment
            start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            duration_minutes: Duration in minutes (default 60)
            description: Description/Notes
            attendee_name: Name of the attendee
            attendee_email: Email of the attendee
            attendee_phone: Phone number
        """
        logger.info(f"Creating appointment: {title} at {start_time}")
        
        try:
            db = SessionLocal()
            start_dt = datetime.fromisoformat(start_time)
            
            # 1. Create Google Calendar Event
            calendar_service = CalendarService(db, self.workspace_id)
            
            # Generate codes first
            appt_id = generate_appointment_id()
            confirm_code = generate_confirmation_code()
            
            # Prepend code to title for visibility
            full_title = f"[{confirm_code}] {title}"
            
            event_data = {
                'summary': full_title,
                'description': f"{description}\n\nConfirmation Code: {confirm_code}",
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': (start_dt + timedelta(minutes=duration_minutes)).isoformat(), 'timeZone': 'UTC'},
                'attendees': []
            }
            
            if attendee_email:
                event_data['attendees'].append({'email': attendee_email})
                
            event = calendar_service.create_event(event_data)
            
            if not event:
                return "Failed to schedule appointment on calendar."
            
            # 2. Find or Create Customer (Deduplication Logic)
            customer = None
            if attendee_email or attendee_phone:
                # Try to find existing customer
                query = db.query(Customer).filter(Customer.workspace_id == self.workspace_id)
                filters = []
                if attendee_email:
                    filters.append(Customer.email == attendee_email)
                if attendee_phone:
                    filters.append(Customer.phone == attendee_phone)
                
                if filters:
                    from sqlalchemy import or_
                    customer = query.filter(or_(*filters)).first()
            
            # Create if not found
            if not customer and (attendee_name or attendee_email):
                customer = Customer(
                    workspace_id=self.workspace_id,
                    first_name=attendee_name.split(" ")[0] if attendee_name else "Unknown",
                    last_name=" ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else "",
                    email=attendee_email,
                    phone=attendee_phone
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
            
            # 3. Create Local Appointment Record
            # [Restored Logic] Link Communication to Real Customer
            if customer and self.communication_id:
                try:
                    comm_record = db.query(Communication).filter(Communication.id == self.communication_id).first()
                    # Only update if not already linked (or linked to guest)
                    if comm_record and comm_record.customer_id != customer.id:
                        logger.info(f"Linking Communication {self.communication_id} to Customer {customer.id}")
                        comm_record.customer_id = customer.id
                        db.commit()
                except Exception as e:
                    logger.error(f"Error linking communication to customer: {e}")

            local_appt = Appointment(
                id=appt_id,
                workspace_id=self.workspace_id,
                customer_id=customer.id if customer else None,
                customer_first_name=attendee_name.split(" ")[0] if attendee_name else None,
                customer_last_name=" ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None,
                customer_email=attendee_email,
                customer_phone=attendee_phone,
                title=title,
                description=description,
                appointment_date=start_dt,
                duration_minutes=duration_minutes,
                status="confirmed",
                calendar_event_id=event.get('id'),
                confirmation_code=confirm_code
            )
            db.add(local_appt)
            db.commit()
            
            # 4. Confirmation (SMS logic would go here)
            sms_status = ""
            
            date_str = start_dt.strftime("%A, %B %d at %I:%M %p")
            return f"Appointment created: '{title}' on {date_str}. Confirmation Code: {confirm_code}."
            
        except Exception as e:
            logger.error(f"Create appointment failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return f"Failed to create appointment: {str(e)}"
        finally:
            db.close()
