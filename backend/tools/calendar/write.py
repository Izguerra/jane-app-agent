import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.database import SessionLocal, generate_appointment_id
from backend.services.calendar_service import CalendarService
from backend.models_db import Appointment
from .verification import CalendarVerification

class CalendarWriteTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    def create_appointment(self, title: str, start_time: str, duration_minutes: int = 60, description: str = "", attendee_name: str = None, attendee_email: str = None, attendee_phone: str = None) -> str:
        db = SessionLocal()
        try:
            if not CalendarVerification.check_permission(db, self.workspace_id, "edit"):
                return "Permission denied: The workspace settings do not allow creating appointments."

            service = CalendarService(db)
            customer = None
            attendees = []
            
            if attendee_email or attendee_phone:
                from backend.services.crm_service import CRMService
                crm_service = CRMService(db)
                customer_data = {
                    "first_name": attendee_name.split(" ")[0] if attendee_name else None,
                    "last_name": " ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None,
                    "email": attendee_email, "phone": attendee_phone, "status": "active", "customer_type": "customer"
                }
                customer = crm_service.create_customer(self.workspace_id, customer_data)
                if customer and customer.email: attendees.append(customer.email)
            
            start_dt = datetime.fromisoformat(start_time)
            bg_tz = ZoneInfo("America/Toronto")
            start_dt = start_dt.replace(tzinfo=bg_tz) if start_dt.tzinfo is None else start_dt.astimezone(bg_tz)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
            appointment_id = generate_appointment_id()
            details = [f"Appointment ID: {appointment_id}"]
            if attendee_name: details.append(f"Customer Name: {attendee_name}")
            if attendee_phone: details.append(f"Phone: {attendee_phone}")
            if attendee_email: details.append(f"Email: {attendee_email}")
            description = f"{'\n'.join(details)}\n\n{description}".strip()
            
            event = service.create_event(self.workspace_id, title, start_dt, end_dt, description, attendees)
            
            appt_record = Appointment(
                id=appointment_id, workspace_id=self.workspace_id, customer_id=customer.id if customer else None,
                customer_first_name=customer.first_name if customer else (attendee_name.split(" ")[0] if attendee_name else None),
                customer_last_name=customer.last_name if customer else (" ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None),
                customer_email=customer.email if customer else attendee_email,
                customer_phone=customer.phone if customer else attendee_phone,
                title=title, description=description, appointment_date=start_dt, duration_minutes=duration_minutes,
                status='confirmed', calendar_event_id=event.get('id')
            )
            db.add(appt_record)
            db.commit()
            
            if appt_record.customer_id:
                from backend.services.crm_service import CRMService
                CRMService(db).update_status_on_appointment(self.workspace_id, appt_record.customer_id)
            
            date_str = start_dt.strftime("%A, %B %d at %I:%M %p")
            sms_status, email_status = "", ""
            
            if attendee_phone:
                from backend.services.sms_service import send_sms
                if send_sms(attendee_phone, f"Appointment Confirmed for {attendee_name}: {title} on {date_str}.", workspace_id=self.workspace_id):
                    sms_status = " SMS confirmation sent."
            
            if attendee_email:
                from backend.services.email_service import EmailService
                EmailService().send_email(to_email=attendee_email, subject=f"Appointment Confirmed for {attendee_name}: {title}", html_content=f"Hi {attendee_name},\nConfirmed: {title} on {date_str}.", workspace_id=self.workspace_id)
                email_status = " Email confirmation sent."
    
            return f"Appointment created: '{event['title']}' on {date_str} (ID: {event['id']}).{sms_status}{email_status}"
        except Exception as e:
            return f"Error creating appointment: {str(e)}"
        finally:
            db.close()

    def cancel_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str) -> str:
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before cancelling appointments."

        db = SessionLocal()
        try:
            if not CalendarVerification.check_permission(db, self.workspace_id, "delete"):
                return "Permission denied: The workspace settings do not allow cancelling appointments."

            service = CalendarService(db)
            event = service.get_event(self.workspace_id, appointment_id.strip())
            if not event: return f"Appointment with ID '{appointment_id}' not found."
                
            is_verified, msg = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified: return f"SECURITY WARNING: {msg}"
            
            if service.delete_event(self.workspace_id, appointment_id.strip()):
                local_appt = db.query(Appointment).filter((Appointment.id == appointment_id) | (Appointment.calendar_event_id == appointment_id), Appointment.workspace_id == self.workspace_id).first()
                if local_appt:
                    local_appt.status = 'cancelled'
                    db.commit()

                start_str = event.get('start', 'Unknown time')
                title = event.get('title', 'Appointment')
                sms_status, email_status = "", ""
                
                if verify_phone:
                    from backend.services.sms_service import send_sms
                    if send_sms(verify_phone, f"Appointment Cancelled for {verify_name}: {title} on {start_str}.", workspace_id=self.workspace_id):
                        sms_status = " SMS cancellation sent."
                
                if verify_email:
                    from backend.services.email_service import EmailService
                    EmailService().send_email(to_email=verify_email, subject=f"Appointment Cancelled for {verify_name}", html_content=f"Hi {verify_name},\nCancelled: {title} on {start_str}.", workspace_id=self.workspace_id)
                    email_status = " Email cancellation sent."
                
                return f"Appointment '{title}' on {start_str} has been successfully cancelled.{sms_status}{email_status}"
            return f"Failed to cancel appointment {appointment_id}."
        except Exception as e:
            return f"Error cancelling appointment: {str(e)}"
        finally:
            db.close()

    def edit_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str, new_start_time: str = None, new_duration_minutes: int = None, new_title: str = None, new_description: str = None) -> str:
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before editing appointments."

        db = SessionLocal()
        try:
            if not CalendarVerification.check_permission(db, self.workspace_id, "edit"):
                return "Permission denied: The workspace settings do not allow editing appointments."

            service = CalendarService(db)
            event = service.get_event(self.workspace_id, appointment_id)
            if not event: return "Appointment not found."
                
            is_verified, msg = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified: return f"SECURITY WARNING: {msg}"
            
            start_dt, end_dt = None, None
            if new_start_time:
                start_dt = datetime.fromisoformat(new_start_time)
                duration = new_duration_minutes or (datetime.fromisoformat(event['end']) - datetime.fromisoformat(event['start'])).total_seconds() / 60
                end_dt = start_dt + timedelta(minutes=duration)
            
            updated_event = service.update_event(self.workspace_id, appointment_id, start_time=start_dt, end_time=end_dt, title=new_title, description=new_description)
            
            local_appt = db.query(Appointment).filter((Appointment.id == appointment_id) | (Appointment.calendar_event_id == appointment_id), Appointment.workspace_id == self.workspace_id).first()
            if local_appt:
                if start_dt:
                    local_appt.appointment_date = start_dt
                    local_appt.duration_minutes = (end_dt - start_dt).total_seconds() / 60 if end_dt else local_appt.duration_minutes
                if new_title: local_appt.title = new_title
                if new_description: local_appt.description = new_description
                db.commit()
            
            start_str = updated_event.get('start')
            sms_status, email_status = "", ""
            if verify_phone:
                from backend.services.sms_service import send_sms
                if send_sms(verify_phone, f"Appointment Modified: {updated_event.get('title')} is now on {start_str}.", workspace_id=self.workspace_id):
                    sms_status = " SMS notification sent."
            if verify_email:
                from backend.services.email_service import EmailService
                EmailService().send_email(to_email=verify_email, subject=f"Appointment Modified: {updated_event.get('title')}", html_content=f"Hi {verify_name},\nModified: {updated_event.get('title')} is now on {start_str}.", workspace_id=self.workspace_id)
                email_status = " Email notification sent."
            
            return f"Appointment updated successfully: '{updated_event['title']}' is now scheduled for {start_str}.{sms_status}{email_status}"
        except Exception as e:
            return f"Error editing appointment: {str(e)}"
        finally:
            db.close()
