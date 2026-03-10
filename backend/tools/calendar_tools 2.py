from agno.agent import Agent
from backend.services.calendar_service import CalendarService
from backend.database import SessionLocal
from sqlalchemy import func
from datetime import datetime, timedelta
import json

class CalendarTools:
    def __init__(self, workspace_id: int, customer_id: str = None):
        self.workspace_id = workspace_id
        self.customer_id = customer_id

    def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None) -> str:
        """
        List appointments for a specific date or today.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        :param date: Date in YYYY-MM-DD format (optional, defaults to today)
        :param verify_name: User's full name (REQUIRED for security)
        :param verify_phone: User's phone number (REQUIRED for security)
        :param verify_email: User's email address (REQUIRED for security)
        :return: JSON string of appointments that match the user's identity
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before showing appointments."
        
        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            if date:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                # Expand range to cover full day + buffer for TZ shifts
                # If user asks for "today", we want 00:00 to 23:59 local, but API might need UTC
                # Best to search a bit wider
                end_dt = start_dt + timedelta(days=1)
            else:
                # Default to today, but look ahead 7 days if no date specified to find upcoming
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(days=7)
            
            events = service.list_events(self.workspace_id, start_dt, end_dt)
            
            if not events:
                return "No appointments found for this date."
            
            # SECURITY: Filter events to only show those matching the user's identity
            user_events = []
            for event in events:
                description = event.get('description', '')
                
                # Parse attendee info from description
                stored_name = None
                stored_phone = None
                stored_email = None
                
                for line in description.split('\n'):
                    line_lower = line.lower().strip()
                    if line_lower.startswith('customer name:'):
                        stored_name = line.split(':', 1)[1].strip()
                    elif line_lower.startswith('phone:'):
                        stored_phone = line.split(':', 1)[1].strip()
                    elif line_lower.startswith('email:'):
                        stored_email = line.split(':', 1)[1].strip()
                
                # Verify identity match (require email OR phone match for security)
                email_match = verify_email and stored_email and verify_email.lower() == stored_email.lower()
                phone_match = verify_phone and stored_phone and ''.join(filter(str.isdigit, verify_phone)) == ''.join(filter(str.isdigit, stored_phone))
                
                if email_match or phone_match:
                    # REDACT PII from description to prevent accidental disclosure
                    # We remove the lines that contain the stored contact info
                    clean_lines = []
                    for line in description.split('\n'):
                        if line.startswith(('Customer Name:', 'Phone:', 'Email:')):
                            continue
                        clean_lines.append(line)
                    
                    # Create a copy of the event to modify
                    safe_event = event.copy()
                    safe_event['description'] = "\n".join(clean_lines).strip()
                    
                    user_events.append(safe_event)
            
            range_msg = f"Search Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
            
            if not user_events:
                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] list_appointments: No events found for {verify_name}\n")
                return f"No appointments found for {verify_name} in range {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}."
            
            json_output = json.dumps(user_events, default=str, indent=2)
            with open("debug_calendar.log", "a") as f:
                f.write(f"[{datetime.now()}] list_appointments output: {json_output}\n")
            return f"{range_msg}\n\n{json_output}"
        except Exception as e:
            return f"Error listing appointments: {str(e)}"
        finally:
            db.close()

    def get_availability(self, date: str = None) -> str:
        """
        Get available time slots for a specific date.
        :param date: Date in YYYY-MM-DD format (optional, defaults to today)
        :return: List of available time slots
        """
        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            if date:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                target_date = datetime.now()
            
            slots = service.get_availability(self.workspace_id, target_date)
            
            if not slots:
                return "No availability information available."
            
            date_str = target_date.strftime("%A, %B %d, %Y")
            return f"Available slots for {date_str}:\n" + "\n".join([f"- {slot}" for slot in slots])
        except Exception as e:
            return f"Error getting availability: {str(e)}"
        finally:
            db.close()

    def _check_permission(self, db, permission_type: str) -> bool:
        """
        Check if the workspace has the required permission enabled in Google Calendar integration.
        permission_type: 'view', 'edit', 'delete'
        """
        from backend.models_db import Integration
        try:
            # Check Google Calendar settings
            integration = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider == "google_calendar",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return False # No integration = no permission (or should we allow strict?)
                
            if not integration.settings:
                return True # Default to allowed if no settings
                
            settings = json.loads(integration.settings) if isinstance(integration.settings, str) else integration.settings
            
            # Map permission types to keys
            key_map = {
                "view": "can_view_own_events",
                "edit": "can_edit_own_events", # Covers create and edit
                "delete": "can_delete_own_events"
            }
            
            key = key_map.get(permission_type)
            if not key: return False
            
            return settings.get(key, False)
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False

    def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None) -> str:
        """
        List appointments for a specific date or today.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        :param date: Date in YYYY-MM-DD format (optional, defaults to today)
        :param verify_name: User's full name (REQUIRED for security)
        :param verify_phone: User's phone number (REQUIRED for security)
        :param verify_email: User's email address (REQUIRED for security)
        :return: JSON string of appointments that match the user's identity
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before showing appointments."
        
        db = SessionLocal()
        try:
            # PERMISSION CHECK
            if not self._check_permission(db, "view"):
                return "Permission denied: The workspace settings do not allow viewing calendar events."
            
            service = CalendarService(db)
            
            if date:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                # Expand range to cover full day + buffer for TZ shifts
                # If user asks for "today", we want 00:00 to 23:59 local, but API might need UTC
                # Best to search a bit wider
                end_dt = start_dt + timedelta(days=1)
            else:
                # Default to today, but look ahead 7 days if no date specified to find upcoming
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(days=7)
            
            events = service.list_events(self.workspace_id, start_dt, end_dt)
            
            if not events:
                return "No appointments found for this date."
            
            # SECURITY: Filter events to only show those matching the user's identity
            user_events = []
            for event in events:
                description = event.get('description', '')
                
                # Parse attendee info from description
                stored_name = None
                stored_phone = None
                stored_email = None
                
                for line in description.split('\n'):
                    line_lower = line.lower().strip()
                    if line_lower.startswith('customer name:'):
                        stored_name = line.split(':', 1)[1].strip()
                    elif line_lower.startswith('phone:'):
                        stored_phone = line.split(':', 1)[1].strip()
                    elif line_lower.startswith('email:'):
                        stored_email = line.split(':', 1)[1].strip()
                
                # Verify identity match (require email OR phone match for security)
                email_match = verify_email and stored_email and verify_email.lower() == stored_email.lower()
                # Determine phone match normalized
                verify_phone_digits = "".join(filter(str.isdigit, verify_phone)) if verify_phone else ""
                stored_phone_digits = "".join(filter(str.isdigit, stored_phone)) if stored_phone else ""
                phone_match = verify_phone_digits and stored_phone_digits and verify_phone_digits == stored_phone_digits
                
                if email_match or phone_match:
                    # REDACT PII from description to prevent accidental disclosure
                    # We remove the lines that contain the stored contact info
                    clean_lines = []
                    for line in description.split('\n'):
                        if line.startswith(('Customer Name:', 'Phone:', 'Email:', 'Appointment ID:')):
                            continue
                        clean_lines.append(line)
                    
                    # Create a copy of the event to modify
                    safe_event = event.copy()
                    safe_event['description'] = "\n".join(clean_lines).strip()
                    
                    # Extract Appointment ID from description if possible for reference
                    # Or rely on 'id' if consistent
                    
                    user_events.append(safe_event)
            
            range_msg = f"Search Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
            
            if not user_events:
                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] list_appointments: No events found for {verify_name}\n")
                return f"No appointments found for {verify_name} in range {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}."
            
            json_output = json.dumps(user_events, default=str, indent=2)
            with open("debug_calendar.log", "a") as f:
                f.write(f"[{datetime.now()}] list_appointments output: {json_output}\n")
            return f"{range_msg}\n\n{json_output}"
        except Exception as e:
            return f"Error listing appointments: {str(e)}"
        finally:
            db.close()

    def get_availability(self, date: str = None) -> str:
        """
        Get available time slots for a specific date.
        :param date: Date in YYYY-MM-DD format (optional, defaults to today)
        :return: List of available time slots
        """
        db = SessionLocal()
        try:
            # PERMISSION CHECK
            if not self._check_permission(db, "view"):
                return "Permission denied: The workspace settings do not allow viewing calendar availability."

            service = CalendarService(db)
            
            if date:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                target_date = datetime.now()
            
            slots = service.get_availability(self.workspace_id, target_date)
            
            if not slots:
                return "No availability information available."
            
            date_str = target_date.strftime("%A, %B %d, %Y")
            return f"Available slots for {date_str}:\n" + "\n".join([f"- {slot}" for slot in slots])
        except Exception as e:
            return f"Error getting availability: {str(e)}"
        finally:
            db.close()

    def create_appointment(self, title: str, start_time: str, duration_minutes: int = 60, description: str = "", attendee_name: str = None, attendee_email: str = None, attendee_phone: str = None) -> str:
        """
        Create a new appointment.
        :param title: Title of the appointment
        :param start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        :param duration_minutes: Duration in minutes (default 60)
        :param description: Description or notes
        :param attendee_name: Name of the attendee (REQUIRED: Pass even for existing customers)
        :param attendee_email: Email of the attendee (REQUIRED: Pass to update customer record)
        :param attendee_phone: Phone number of the attendee (REQUIRED: Pass to update customer record)
        :return: Confirmation message
        """
        db = SessionLocal()
        try:
            # PERMISSION CHECK
            if not self._check_permission(db, "edit"):
                return "Permission denied: The workspace settings do not allow creating appointments."

            service = CalendarService(db)
            
            # Handle Customer creation/update
            # Handle Customer creation/update
            attendees = []
            if attendee_email or attendee_phone:
                from backend.models_db import Customer
                from backend.services.crm_service import CRMService
                crm_service = CRMService(db)
                
                # Use centralized CRM logic to find or create customer
                # This ensures consistent strict uniqueness rules (Email Primary, Phone Secondary)
                customer_data = {
                    "first_name": attendee_name.split(" ")[0] if attendee_name else None,
                    "last_name": " ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None,
                    "email": attendee_email,
                    "phone": attendee_phone,
                    "status": "active",
                    "customer_type": "customer"
                }
                
                # If we have a session-based customer_id, try to use it?
                # Actually create_customer doesn't take ID. The service logic handles looking up by email/phone.
                # But we might want to "promote" the current session user if possible.
                # However, create_customer is stateless regarding session.
                # Let's trust the strict email/phone lookup.
                
                customer = crm_service.create_customer(self.workspace_id, customer_data)
                print(f"DEBUG: Resolved customer for appointment: {customer.id}")
                
                if customer and customer.email:
                    attendees.append(customer.email)
            
            start_dt = datetime.fromisoformat(start_time)
            
            # TIMEZONE FIX: Force interpretation as America/Toronto (EST/EDT)
            from zoneinfo import ZoneInfo
            bg_tz = ZoneInfo("America/Toronto")
            
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=bg_tz)
            else:
                start_dt = start_dt.astimezone(bg_tz)

            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
            # Generate appointment ID first
            from backend.models_db import Appointment
            from backend.database import generate_appointment_id
            
            appointment_id = generate_appointment_id()
            
            # Append customer details to description
            details_parts = []
            details_parts.append(f"Appointment ID: {appointment_id}")
            if attendee_name: details_parts.append(f"Customer Name: {attendee_name}")
            if attendee_phone: details_parts.append(f"Phone: {attendee_phone}")
            if attendee_email: details_parts.append(f"Email: {attendee_email}")
            
            if details_parts:
                contact_info = "\n".join(details_parts)
                description = f"{contact_info}\n\n{description}".strip()
            
            # Create calendar event
            event = service.create_event(self.workspace_id, title, start_dt, end_dt, description, attendees)
            
            # Create Appointment record in database
            appointment_record = Appointment(
                id=appointment_id,
                workspace_id=self.workspace_id,
                customer_id=customer.id if customer else None,
                customer_first_name=customer.first_name if customer else (attendee_name.split(" ")[0] if attendee_name else None),
                customer_last_name=customer.last_name if customer else (" ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None),
                customer_email=customer.email if customer else attendee_email,
                customer_phone=customer.phone if customer else attendee_phone,
                title=title,
                description=description,
                appointment_date=start_dt,
                duration_minutes=duration_minutes,
                status='confirmed',
                calendar_event_id=event.get('id'),
                location=None,
                notes=None
            )
            db.add(appointment_record)
            db.commit()
            
            # CRM Status Update
            try:
                if appointment_record.customer_id:
                     from backend.services.crm_service import CRMService
                     crm_service = CRMService(db)
                     crm_service.update_status_on_appointment(self.workspace_id, appointment_record.customer_id)
            except Exception as e:
                print(f"[CRM_ERROR] Failed to update CRM status: {e}")
            
            # Format Date for Notifications
            date_str = start_dt.strftime("%A, %B %d at %I:%M %p")
            
            # 1. SMS Notification
            sms_status = ""
            if attendee_phone:
                try:
                    from backend.services.sms_service import send_sms
                    sms_body = f"Appointment Confirmed for {attendee_name}: {title} on {date_str}."
                    if send_sms(attendee_phone, sms_body, workspace_id=self.workspace_id):
                        sms_status = " SMS confirmation sent."
                    else:
                        sms_status = " SMS confirmation failed."
                except Exception as e:
                    sms_status = f" SMS error: {str(e)}"
            
            # 2. Email Notification
            email_status = ""
            if attendee_email:
                try:
                    from backend.services.email_service import EmailService
                    email_service = EmailService()
                    
                    email_subject = f"Appointment Confirmed for {attendee_name}: {title}"
                    email_body = f"""
                    Hi {attendee_name},
                    
                    Your appointment has been confirmed.
                    
                    **Details:**
                    - **Service:** {title}
                    - **Date & Time:** {date_str}
                    - **Appointment ID:** {appointment_id}
                    
                    Thank you!
                    """
                    # Use a generic sender or default
                    email_service.send_email(to_email=attendee_email, subject=email_subject, html_content=email_body, workspace_id=self.workspace_id)
                    email_status = " Email confirmation sent."
                except Exception as e:
                    print(f"[EMAIL ERROR] Failed to send email: {e}")
                    email_status = f" Email error: {str(e)}"
    
            return f"Appointment created: '{event['title']}' on {date_str} (ID: {event['id']}).{sms_status}{email_status}"
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[CALENDAR_ERROR] Failed to create appointment: {str(e)}\n{error_trace}")
            return f"Error creating appointment: {str(e)}"
        finally:
            db.close()

    def cancel_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str) -> str:
        """
        Cancel an appointment by ID.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        :param appointment_id: ID of the appointment to cancel
        :param verify_name: User's full name (REQUIRED for security)
        :param verify_phone: User's phone number (REQUIRED for security)
        :param verify_email: User's email address (REQUIRED for security)
        :return: Confirmation message
        """
        print(f"DEBUG: cancel_appointment called with ID: {appointment_id}")
        
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before cancelling appointments."

        db = SessionLocal()
        try:
            # PERMISSION CHECK
            if not self._check_permission(db, "delete"):
                return "Permission denied: The workspace settings do not allow cancelling appointments."

            service = CalendarService(db)
            
            # 1. Fetch event to verify ownership
            event = service.get_event(self.workspace_id, appointment_id.strip())
            if not event:
                return f"Appointment with ID '{appointment_id}' not found."
                
            # 2. Verify Identity
            is_verified, message = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified:
                return f"SECURITY WARNING: {message}"
            
            # 3. Delete External Event
            success = service.delete_event(self.workspace_id, appointment_id.strip())
            if success:
                # 4. DB Sync: Cancel local record
                from backend.models_db import Appointment
                
                # Try to find by calendar_event_id (if appointment_id is actually the google ID)
                # Or if appointment_id is our internal ID.
                # The prompt uses "appointment_id". 
                # If we stored our internal ID in description, we often use that to lookup.
                # However, `service.delete_event` expects the GOOGLE ID usually?
                # Wait, `get_event` returns the object.
                # Let's try to update the DB based on matching valid fields.
                
                local_appt = db.query(Appointment).filter(
                    (Appointment.id == appointment_id) | (Appointment.calendar_event_id == appointment_id),
                    Appointment.workspace_id == self.workspace_id
                ).first()
                
                if local_appt:
                    local_appt.status = 'cancelled'
                    db.commit()
                    print(f"DEBUG: Local appointment {local_appt.id} marked as cancelled.")

                # Format event details for feedback
                start_str = event.get('start', 'Unknown time')
                if isinstance(start_str, str):
                    try:
                        dt = datetime.fromisoformat(start_str)
                        start_str = dt.strftime("%A, %B %d at %I:%M %p")
                    except:
                        pass
                
                title = event.get('title', 'Appointment')
            
                # 5. Notifications (SMS + Email)
                sms_status = ""
                email_status = ""
                
                # SMS
                if verify_phone:
                    try:
                        from backend.services.sms_service import send_sms
                        sms_body = f"Appointment Cancelled for {verify_name}: {title} on {start_str}."
                        if send_sms(verify_phone, sms_body, workspace_id=self.workspace_id):
                            sms_status = " SMS cancellation sent."
                    except Exception as e:
                        sms_status = f" SMS error: {str(e)}"
                
                # Email
                if verify_email:
                    try:
                        from backend.services.email_service import EmailService
                        email_service = EmailService()
                        email_subject = f"Appointment Cancelled for {verify_name}"
                        email_body = f"""
                        Hi {verify_name},
                        
                        Your appointment has been cancelled.
                        
                        **Details:**
                        - **Service:** {title}
                        - **Date & Time:** {start_str}
                        
                        If this was a mistake, please contact us to reschedule.
                        """
                        email_service.send_email(to_email=verify_email, subject=email_subject, html_content=email_body, workspace_id=self.workspace_id)
                        email_status = " Email cancellation sent."
                    except Exception as e:
                        email_status = f" Email error: {str(e)}"
                
                return f"Appointment '{title}' on {start_str} has been successfully cancelled.{sms_status}{email_status}"
            else:
                return f"Failed to cancel appointment {appointment_id}."
        except Exception as e:
            return f"Error cancelling appointment: {str(e)}"
        finally:
            db.close()

    def edit_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str, new_start_time: str = None, new_duration_minutes: int = None, new_title: str = None, new_description: str = None) -> str:
        """
        Edit an existing appointment.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        :param appointment_id: ID of the appointment to edit
        :param verify_name: User's full name (REQUIRED for security)
        :param verify_phone: User's phone number (REQUIRED for security)
        :param verify_email: User's email address (REQUIRED for security)
        :param new_start_time: New start time in ISO format (optional)
        :param new_duration_minutes: New duration in minutes (optional)
        :param new_title: New title (optional)
        :param new_description: New description (optional)
        :return: Confirmation message
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before editing appointments."

        db = SessionLocal()
        try:
            # PERMISSION CHECK
            if not self._check_permission(db, "edit"):
                return "Permission denied: The workspace settings do not allow editing appointments."

            service = CalendarService(db)
            
            # 1. Fetch event
            event = service.get_event(self.workspace_id, appointment_id)
            if not event:
                return "Appointment not found."
                
            # 2. Verify Identity
            is_verified, message = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified:
                return f"SECURITY WARNING: {message}"
            
            # 3. Calculate new times
            start_dt = None
            end_dt = None
            
            if new_start_time:
                start_dt = datetime.fromisoformat(new_start_time)
                # Determine duration
                if new_duration_minutes:
                    duration = new_duration_minutes
                else:
                    old_start = datetime.fromisoformat(event['start']) if isinstance(event['start'], str) else event['start']
                    old_end = datetime.fromisoformat(event['end']) if isinstance(event['end'], str) else event['end']
                    duration = (old_end - old_start).total_seconds() / 60
                end_dt = start_dt + timedelta(minutes=duration)
            
            # 4. Update External Event
            updated_event = service.update_event(
                self.workspace_id, 
                appointment_id, 
                start_time=start_dt, 
                end_time=end_dt, 
                title=new_title, 
                description=new_description
            )
            
            # 5. DB Sync: Update local record
            from backend.models_db import Appointment
            local_appt = db.query(Appointment).filter(
                (Appointment.id == appointment_id) | (Appointment.calendar_event_id == appointment_id),
                Appointment.workspace_id == self.workspace_id
            ).first()
            
            if local_appt:
                if start_dt:
                    local_appt.appointment_date = start_dt
                    local_appt.duration_minutes = (end_dt - start_dt).total_seconds() / 60 if end_dt else local_appt.duration_minutes
                if new_title:
                    local_appt.title = new_title
                if new_description:
                    local_appt.description = new_description
                
                db.commit()
                print(f"DEBUG: Local appointment {local_appt.id} updated.")
            
            # Format output
            start_str = updated_event.get('start')
            if isinstance(start_str, str):
                try:
                    dt = datetime.fromisoformat(start_str)
                    start_str = dt.strftime("%A, %B %d at %I:%M %p")
                except:
                    pass
            
            # 6. Notifications (SMS + Email)
            sms_status = ""
            email_status = ""
            
            # SMS
            if verify_phone:
                try:
                    from backend.services.sms_service import send_sms
                    title_chk = updated_event.get('title', 'Your appointment')
                    sms_body = f"Appointment Modified for {verify_name}: {title_chk} is now on {start_str}."
                    if send_sms(verify_phone, sms_body, workspace_id=self.workspace_id):
                        sms_status = " SMS notification sent."
                except Exception as e:
                    sms_status = f" SMS error: {str(e)}"
            
            # Email
            if verify_email:
                try:
                    from backend.services.email_service import EmailService
                    email_service = EmailService()
                    title_chk = updated_event.get('title', 'Your appointment')
                    email_subject = f"Appointment Modified for {verify_name}: {title_chk}"
                    email_body = f"""
                    Hi {verify_name},
                    
                    Your appointment has been modified.
                    
                    **New Details:**
                    - **Service:** {title_chk}
                    - **Date & Time:** {start_str}
                    
                    If this wasn't you, please contact us immediately.
                    """
                    email_service.send_email(to_email=verify_email, subject=email_subject, html_content=email_body, workspace_id=self.workspace_id)
                    email_status = " Email notification sent."
                except Exception as e:
                    email_status = f" Email error: {str(e)}"
            
            return f"Appointment updated successfully: '{updated_event['title']}' is now scheduled for {start_str}.{sms_status}{email_status}"
        except Exception as e:
            return f"Error editing appointment: {str(e)}"
        finally:
            db.close()
