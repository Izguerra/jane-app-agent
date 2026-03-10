import random
from livekit.agents import llm
import importlib
import pkgutil
import inspect
from pathlib import Path

_WORKER_REGISTRY_CACHE = {}

def get_worker_handler(w_type: str):
    """
    Global Registry resolving worker slugs to their executable methods.
    Uses DYNAMIC DISCOVERY to find workers in backend/workers/.
    """
    global _WORKER_REGISTRY_CACHE
    
    # Normalize slug
    slug = w_type.lower().strip()
    
    # Check cache first
    if slug in _WORKER_REGISTRY_CACHE:
        return _WORKER_REGISTRY_CACHE[slug]
    
    # If not in cache, scan (lazy load)
    workers_dir = Path(__file__).parent / "workers"
    if not workers_dir.exists():
         print(f"ERROR: Workers directory not found at {workers_dir}")
         return None

    # Helper to register
    def register(key, handler):
        _WORKER_REGISTRY_CACHE[key] = handler

    # Scan
    for file in workers_dir.glob("*_worker.py"):
        module_name = f"backend.workers.{file.stem}"
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith("Worker") and name != "BaseEnterpriseWorker":
                    file_slug = file.stem.replace("_", "-")
                    method = getattr(obj, "run", getattr(obj, "execute", None))
                    if method:
                        register(file_slug, method)
                        short_slug = file_slug.replace("-worker", "")
                        if short_slug != file_slug:
                             register(short_slug, method)
                        
                        if "email" in file_slug:
                             register("email-assistant", method)
                             register("email-management", method)
                        if "map" in file_slug:
                             register("navigation-assistant", method)
                             register("directions", method)
                        if "sms" in file_slug:
                             register("sms-worker", method)
                        if "translation" in file_slug:
                             register("translation-localization", method)
                        if "compliance" in file_slug:
                             register("compliance-risk", method)
        except Exception as e:
            print(f"Warning: Failed to load worker module {module_name}: {e}")

    if slug in _WORKER_REGISTRY_CACHE:
        return _WORKER_REGISTRY_CACHE[slug]
    return None

class AgentTools:
    def __init__(self, workspace_id: str, customer_id: str = None, communication_id: str = None, agent_id: str = None, worker_tools=None):
        self.workspace_id = workspace_id
        self.customer_id = customer_id
        self.communication_id = communication_id
        self.agent_id = agent_id
        self.worker_tools = worker_tools # Unified validation layer
        self.session = None # Injected by Voice Agent

    async def _play_filler(self, message: str = "One moment please..."):
        """Plays a filler message to bridge latency for slow tools"""
        if hasattr(self, 'session') and self.session:
            try:
                if hasattr(self.session, 'say'):
                    self.session.say(message, allow_interruptions=False, add_to_chat_ctx=False)
                    print(f"🔊 Playing filler audio: {message}")
            except Exception as e:
                print(f"🔊 Failed to play filler audio: {e}")



    @llm.function_tool(
        description="Search the knowledge base for information about the business, policies, or specific documents.",
    )
    async def search_knowledge_base(self, query: str):
        """
        Search the knowledge base for relevant documents.
        Args:
            query: The search query.
        """
        import random
        await self._play_filler(random.choice(["Let me check the knowledge base...", "Checking my resources...", "Looking that up..."]))
        
        from backend.knowledge_base import KnowledgeBaseService
        try:
            kb_service = KnowledgeBaseService()
            results = kb_service.search(query, workspace_id=self.workspace_id)
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            # Format results
            context = "\n\n".join([f"Source: {res.get('filename', 'Unknown')}\nContent: {res.get('text', '')}" for res in results])
            return context
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"

    # --- EXTERNAL TOOLS (Weather, Flights, Maps, Web) ---
    
    @llm.function_tool(
        description="Search the web for real-time information, news, and facts using Tavily. Use this when the knowledge base doesn't have the answer.",
    )
    async def web_search(self, query: str, max_results: int = 5):
        """
        Search the web for real-time info.
        Args:
            query: The search query or question.
            max_results: Number of results to return (1-10).
        """
        import random
        await self._play_filler(random.choice(["Searching the web for that...", "Let me scour the web for you...", "Looking that up online..."]))

        try:
            from backend.tools.web_search import get_web_search_tool
            tool = get_web_search_tool()
            results = tool.search(query, max_results=max_results)
            
            if "error" in results:
                return f"Error during web search: {results['error']}"
                
            # Format results
            output = f"Web Search Results for: {query}\n"
            if results.get("answer"):
                output += f"AI Summary: {results['answer']}\n\n"
                
            for i, r in enumerate(results.get("results", []), 1):
                output += f"{i}. {r.get('title')} - {r.get('url')}\n"
                output += f"   {r.get('content', '')[:300]}...\n\n"
                
            return output if results.get("results") else "No relevant web results found."
        except Exception as e:
            return f"Failed to perform web search: {str(e)}"

    
    @llm.function_tool(
        description="Get current weather for a location. Supports forecasts and specific units.",
    )
    async def get_weather(self, location: str, date: str = None, units: str = "metric"):
        """
        Get current weather for a location.
        Args:
            location: City or region name (e.g. "Milton" or "New York")
            date: Future date in YYYY-MM-DD format (optional)
            units: "metric" (C) or "imperial" (F)
        """
        if self.worker_tools and self.worker_tools.allowed_worker_types and "weather-worker" not in self.worker_tools.allowed_worker_types:
            print(f"🚫 BLOCKED: Tool 'get_weather' requires 'weather-worker'. Allowed: {self.worker_tools.allowed_worker_types}")
            return "Error: The weather tool is not enabled for this agent."

        await self._play_filler(random.choice(["Checking the weather for you...", "Looking up the local forecast...", "Getting the weather info..."]))

        # Always use ExternalTools directly (bypass Worker layer for speed/reliability)
        from backend.tools.external_tools import ExternalTools
        tools = ExternalTools(workspace_id=self.workspace_id)
        return await tools.get_current_weather(location, date=date, units=units)

    @llm.function_tool(
        description="Get status of a flight. You can search by Flight Number (e.g. AA123) OR by Route (Origin, Destination, Airline).",
    )
    async def get_flight_status(self, flight_number: str = None, origin: str = None, destination: str = None, airline: str = None, date: str = None, approx_time: str = None):
        """
        Get flight status.
        Args:
            flight_number: Flight IATA code (e.g. "AC417", "UA123") - Optional.
            origin: City Name (e.g. "Toronto") OR 3-letter Airport Code (e.g. "YYZ")
            destination: City Name (e.g. "Montreal") OR 3-letter Airport Code (e.g. "YUL")
            airline: Airline Name or Code (e.g. "Air Canada") - Optional.
            date: Date in YYYY-MM-DD format (optional).
            approx_time: Approximate time for schedule search (e.g. "5pm", "17:00")
        """
        if self.worker_tools and self.worker_tools.allowed_worker_types and "flight-tracker" not in self.worker_tools.allowed_worker_types:
            print(f"🚫 BLOCKED: Tool 'get_flight_status' requires 'flight-tracker'. Allowed: {self.worker_tools.allowed_worker_types}")
            return "Error: The flight tracking tool is not enabled for this agent."

        await self._play_filler(random.choice(["Checking the flight status...", "Looking up those flight details...", "Checking the skies for you..."]))

        from backend.tools.external_tools import ExternalTools
        tools = ExternalTools(workspace_id=self.workspace_id)
        return await tools.get_flight_status(flight_number, origin, destination, airline, date=date, approx_time=approx_time)

    @llm.function_tool(
        description="Get directions and traffic estimation between two locations",
    )
    async def get_directions(self, origin: str, destination: str, mode: str = "driving"):
        """
        Get directions and traffic info.
        Args:
            origin: Starting point (Specific address or Postal Code preferred)
            destination: Destination
            mode: Mode of transport ("driving", "walking", "bicycling", "transit"). Default is "driving".
        """
        # The condition `self.worker_tools.allowed_worker_types` evaluates to False if the list is empty,
        # effectively allowing the tool when the list is empty.
        if self.worker_tools and self.worker_tools.allowed_worker_types and "map-worker" not in self.worker_tools.allowed_worker_types:
            print(f"🚫 BLOCKED: Tool 'get_directions' requires 'map-worker'. Allowed: {self.worker_tools.allowed_worker_types}")
            return "Error: The directions tool is not enabled for this agent."

        await self._play_filler(random.choice(["Checking the best route for you...", "Looking up those directions...", "Calculating your travel time..."]))

        from backend.tools.external_tools import ExternalTools
        tools = ExternalTools(workspace_id=self.workspace_id)
        return await tools.get_directions(origin, destination, mode)

    @llm.function_tool(
        description="Check the status of a user's application",
    )
    async def check_application_status(self, application_id: str):
        """
        Check the status of a credit application.
        Args:
            application_id: The ID of the application to check.
        """
        # Mock status check
        statuses = ["pending", "approved", "rejected", "under_review"]
        status = random.choice(statuses)
        
        return f"Application {application_id} is currently {status}."

    @llm.function_tool(
        description="List calendar appointments for a specific date. REQUIRES identity verification - you must ask for and provide the user's full name, phone number, and email address.",
    )
    async def list_appointments(self, date: str = None, verify_name: str = None, verify_phone: str = None, verify_email: str = None):
        """
        List appointments for a specific date or today.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        Args:
            date: Date in YYYY-MM-DD format (optional, defaults to today)
            verify_name: User's full name (REQUIRED for security)
            verify_phone: User's phone number (REQUIRED for security)
            verify_email: User's email address (REQUIRED for security)
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before showing appointments."
        
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        from datetime import datetime, timedelta

        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            if date:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                # Expand range to cover full day + buffer for TZ shifts
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
                # Verify identity match (require email OR phone match for security)
                # Normalize inputs
                norm_verify_email = verify_email.replace(" ", "").lower() if verify_email else ""
                norm_stored_email = stored_email.replace(" ", "").lower() if stored_email else ""
                
                norm_verify_phone = ''.join(filter(str.isdigit, verify_phone)) if verify_phone else ""
                norm_stored_phone = ''.join(filter(str.isdigit, stored_phone)) if stored_phone else ""

                email_match = norm_verify_email and norm_stored_email and norm_verify_email == norm_stored_email
                phone_match = norm_verify_phone and norm_stored_phone and (norm_verify_phone == norm_stored_phone or norm_verify_phone in norm_stored_phone or norm_stored_phone in norm_verify_phone)
                
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

                    # --- KEY FIX: Link Communication to Real Customer on Verification ---
                    if not self.customer_id and self.communication_id and verify_email:
                        try:
                            from backend.models_db import Customer, Communication
                            from sqlalchemy import func
                            
                            # Find the customer by verified email
                            customer = db.query(Customer).filter(
                                Customer.workspace_id == self.workspace_id,
                                func.lower(Customer.email) == verify_email.lower()
                            ).first()
                            
                            if customer:
                                comm_record = db.query(Communication).filter(Communication.id == self.communication_id).first()
                                if comm_record and comm_record.customer_id != customer.id:
                                    print(f"DEBUG: Linking Communication {self.communication_id} to Customer {customer.id} (List)")
                                    comm_record.customer_id = customer.id
                                    # Update session customer_id
                                    self.customer_id = customer.id
                                    db.commit()
                        except Exception as e:
                            print(f"Error linking communication in list: {e}")
                    # -----------------------------------------------------------
            
            range_msg = f"Search Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
            
            if not user_events:
                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] list_appointments: No events found for {verify_name}\n")
                return f"No appointments found for {verify_name} in range {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}."
            
            import json
            json_output = json.dumps(user_events, default=str, indent=2)
            with open("debug_calendar.log", "a") as f:
                f.write(f"[{datetime.now()}] list_appointments output: {json_output}\n")
            return f"{range_msg}\n\n{json_output}"
        except Exception as e:
            return f"Error listing appointments: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Get available time slots for a specific date",
    )
    async def get_availability(self, date: str = None):
        """
        Get available time slots for a specific date.
        Args:
            date: Date in YYYY-MM-DD format (optional, defaults to today)
        """
        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        from datetime import datetime

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

    @llm.function_tool(
        description="Create a new calendar appointment",
    )
    async def create_appointment(self, title: str, start_time: str, duration_minutes: int = 60, description: str = "", attendee_name: str = None, attendee_email: str = None, attendee_phone: str = None):
        """
        Create a new appointment.
        Args:
            title: Title of the appointment
            start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            duration_minutes: Duration in minutes (default 60)
            description: Description or notes
            attendee_name: Name of the attendee
            attendee_email: Email of the attendee
            attendee_phone: Phone number of the attendee
        """
        from backend.database import SessionLocal, generate_customer_id, generate_appointment_id
        from backend.services.calendar_service import CalendarService
        from backend.models_db import Customer, Appointment
        from datetime import datetime, timedelta

        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            # Handle Customer creation/update
            attendees = []
            
            # Use CRM Service for robust customer handling
            from backend.services.crm_service import CRMService
            crm = CRMService(db)
            
            customer = None
            
            # 1. Check if we have a current session customer (Guest or Real)
            if self.customer_id:
                current_customer = db.query(Customer).filter(Customer.id == self.customer_id, Customer.workspace_id == self.workspace_id).first()
                
                # If current session is a GUEST, try to promote/merge
                if current_customer and (current_customer.id.startswith("guest_") or current_customer.customer_type == "guest"):
                    if attendee_email or attendee_phone:
                        # Attempt promotion (handles merging if email/phone exists)
                        print(f"DEBUG: Attempting to promote guest {self.customer_id} with new info")
                        customer = crm.promote_guest_to_customer(
                            guest_id=self.customer_id, 
                            new_email=attendee_email, 
                            new_phone=attendee_phone, 
                            new_name=attendee_name
                        )
                        # If promotion returned a new/merged customer, verify/update self.customer_id for this session?
                        # We can't update self.customer_id easily if this tool is stateless, but the tool instance persists for the session.
                        if customer:
                            self.customer_id = customer.id
                else:
                    customer = current_customer
            
            # 2. If no customer yet (or promotion failed?), try to match existing by email/phone ROBUSTLY
            if not customer:
                if attendee_email:
                    from sqlalchemy import func
                    customer = db.query(Customer).filter(func.lower(Customer.email) == attendee_email.lower(), Customer.workspace_id == self.workspace_id).first()
                
                if not customer and attendee_phone:
                    # Robust phone check: generate common formats to match against DB
                    from sqlalchemy import or_
                    clean_phone = attendee_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
                    
                    # Store variations to check
                    phone_variations = [
                        clean_phone,
                        f"+{clean_phone}",
                        f"1{clean_phone}", 
                        f"+1{clean_phone}",
                    ]
                    
                    # Add formatted variations if length is 10 (North American standard)
                    if len(clean_phone) == 10:
                        area = clean_phone[:3]
                        prefix = clean_phone[3:6]
                        line = clean_phone[6:]
                        phone_variations.extend([
                            f"{area}-{prefix}-{line}",
                            f"({area}) {prefix}-{line}",
                            f"1-{area}-{prefix}-{line}",
                            f"+1-{area}-{prefix}-{line}",
                            f"{area} {prefix} {line}"
                        ])
                    
                    customer = db.query(Customer).filter(
                        Customer.workspace_id == self.workspace_id,
                        Customer.phone.in_(phone_variations)
                    ).first()
            
            # 3. If still no customer, Create New
            if not customer:
                 # Standard create
                 customer = Customer(
                    id=llm.generate_customer_id() if hasattr(llm, 'generate_customer_id') else generate_customer_id(), # import check
                    workspace_id=self.workspace_id,
                    first_name=attendee_name.split(" ")[0] if attendee_name else None,
                    last_name=" ".join(attendee_name.split(" ")[1:]) if attendee_name and " " in attendee_name else None,
                    email=attendee_email,
                    phone=attendee_phone,
                    status="active",
                    customer_type="b2c"
                )
                 db.add(customer)
                 db.commit()
                 
            # 4. Final update of existing customer if just found/not promoted
            elif customer and not customer.id.startswith("guest_"):
                 # Update missing fields only? Or overwrite? 
                 # Let's ensure email is set if provided
                 changed = False
                 if attendee_email and not customer.email:
                     customer.email = attendee_email
                     changed = True
                 if attendee_phone and not customer.phone:
                     customer.phone = attendee_phone
                     changed = True
                 if attendee_name and (not customer.first_name or customer.first_name == "Guest"):
                     parts = attendee_name.split(" ")
                     customer.first_name = parts[0]
                     if len(parts) > 1: customer.last_name = " ".join(parts[1:])
                     changed = True
                     
                 if changed:
                     db.commit()

            # --- KEY FIX: Link Communication to Real Customer ---
            if customer and self.communication_id:
                try:
                    from backend.models_db import Communication
                    comm_record = db.query(Communication).filter(Communication.id == self.communication_id).first()
                    if comm_record and comm_record.customer_id != customer.id:
                        print(f"DEBUG: Linking Communication {self.communication_id} to Customer {customer.id}")
                        comm_record.customer_id = customer.id
                        db.commit()
                except Exception as e:
                    print(f"Error linking communication to customer: {e}")
            # ----------------------------------------------------

            if customer and customer.email:
                attendees.append(customer.email)
            
            # Append customer details to description for easy verification
            details_parts = []
            if attendee_name:
                details_parts.append(f"Customer Name: {attendee_name}")
            if attendee_phone:
                details_parts.append(f"Phone: {attendee_phone}")
            if attendee_email:
                details_parts.append(f"Email: {attendee_email}")
            
            if details_parts:
                contact_info = "\n".join(details_parts)
                description = f"{contact_info}\n\n{description}".strip()

            try:
                # ZONE FIX: Force input time to be interpreted as America/Toronto (Business Time)
                # The LLM usually outputs naive ISO strings like "2026-01-06T15:00:00" for "3pm"
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("America/Toronto")
                
                # Parse naive
                start_dt = datetime.fromisoformat(start_time)
                
                # If naive, assume it's Toronto time and attach tz info
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=tz)
                    print(f"DEBUG: Converted naive input {start_time} to {start_dt}")
                else:
                    # If already aware (rare), ensure it's converted to Toronto for consistency
                    start_dt = start_dt.astimezone(tz)

                end_dt = start_dt + timedelta(minutes=duration_minutes)
            except Exception as e:
                return f"Error parsing date/time: {e}"

            event = service.create_event(self.workspace_id, title, start_dt, end_dt, description, attendees)
            
            # Create local Appointment record for valid database tracking
            local_appt = Appointment(
                id=generate_appointment_id(),
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
                calendar_event_id=event.get('id')
            )
            db.add(local_appt)
            db.commit()
            
            # TRIGGER LEAD -> CUSTOMER CONVERSION (PEER REVIEWED)
            try:
                if local_appt.customer_id:
                    print(f"DEBUG: Triggering conversion check for {local_appt.customer_id} after appointment creation")
                    crm.update_status_on_appointment(self.workspace_id, local_appt.customer_id)
            except Exception as e:
                print(f"DEBUG: CRM status update failed: {e}")
            
            # Send SMS Confirmation
            sms_status = ""
            if attendee_phone:
                print(f"DEBUG: Attempting to send SMS to {attendee_phone}")
                try:
                    from backend.services.sms_service import send_sms
                    
                    # Format date for message
                    date_str = start_dt.strftime("%A, %B %d at %I:%M %p")
                    sms_body = f"Hi {attendee_name or 'there'}, your appointment '{title}' is confirmed for {date_str}."
                    
                    print(f"DEBUG: SMS body: {sms_body}")
                    result = send_sms(attendee_phone, sms_body, self.workspace_id)
                    print(f"DEBUG: SMS send result: {result}")
                    
                    if result:
                        sms_status = " SMS confirmation sent."
                    else:
                        sms_status = " SMS confirmation failed (check configuration)."
                except Exception as e:
                    print(f"DEBUG: SMS exception: {type(e).__name__}: {e}")
                    sms_status = f" SMS error: {str(e)}"
            else:
                print(f"DEBUG: No attendee_phone provided, skipping SMS")

            # Fallback date_str if SMS block didn't run or failed
            if 'date_str' not in locals():
                date_str = start_dt.strftime("%A, %B %d at %I:%M %p")

            return f"Appointment created: '{event['title']}' on {date_str} (ID: {event['id']}).{sms_status}"
        except Exception as e:
            return f"Error creating appointment: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Cancel an appointment. REQUIRES identity verification - you must ask for and provide the user's full name, phone number, and email address.",
    )
    async def cancel_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str):
        """
        Cancel an appointment by ID.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        Args:
            appointment_id: ID of the appointment to cancel
            verify_name: User's full name (REQUIRED for security)
            verify_phone: User's phone number (REQUIRED for security)
            verify_email: User's email address (REQUIRED for security)
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before cancelling appointments."

        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService

        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            # 1. Resolve Appointment ID (Local -> Google/External)
            from backend.models_db import Appointment
            from sqlalchemy import or_
            
            clean_id = appointment_id.strip()
            
            local_appt = db.query(Appointment).filter(
                Appointment.workspace_id == self.workspace_id,
                or_(Appointment.id == clean_id, Appointment.calendar_event_id == clean_id)
            ).first()
            
            resolved_event_id = clean_id
            if local_appt and local_appt.calendar_event_id:
                resolved_event_id = local_appt.calendar_event_id
                print(f"DEBUG: Resolved Local ID {clean_id} to External ID {resolved_event_id}")

            # 2. Fetch event to verify ownership
            event = service.get_event(self.workspace_id, resolved_event_id)
            if not event:
                 # Fallback
                 if resolved_event_id != clean_id:
                     event = service.get_event(self.workspace_id, clean_id)
                 
                 if not event:
                    with open("debug_calendar.log", "a") as f:
                        f.write(f"[{datetime.now()}] Appointment '{appointment_id}' not found via service.get_event\n")
                    return f"Appointment with ID '{appointment_id}' not found."
                
            # 2. Verify Identity
            is_verified, message = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified:
                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] Verification failed: {message}\n")
                return f"SECURITY WARNING: {message}"
            
            # 3. Delete
            success = service.delete_event(self.workspace_id, resolved_event_id)
            if success:
                # Also delete from local DB if exists
                from sqlalchemy import or_
                local_appt = db.query(Appointment).filter(
                    Appointment.workspace_id == self.workspace_id,
                    or_(Appointment.id == clean_id, Appointment.calendar_event_id == clean_id)
                ).first()
                
                if local_appt:
                    print(f"DEBUG: Deleting local appointment {local_appt.id} (matched {clean_id})")
                    db.delete(local_appt)
                    db.commit()
                else:
                    # Fallback Search: If we resolved to a Google ID, try finding by calendar_event_id explicitly again
                     fallback_appt = db.query(Appointment).filter(
                        Appointment.workspace_id == self.workspace_id,
                        Appointment.calendar_event_id == resolved_event_id
                    ).first()
                     if fallback_appt:
                        print(f"DEBUG: Deleting local appointment {fallback_appt.id} found via fallback calendar_event_id {resolved_event_id}")
                        db.delete(fallback_appt)
                        db.commit()
                     else:
                        print(f"DEBUG: Failed to find local appointment to delete for ID {clean_id} / {resolved_event_id}")

                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] Appointment '{appointment_id}' cancelled successfully\n")
                
                # Format event details for feedback
                start_str = event.get('start', 'Unknown time')
                if isinstance(start_str, str):
                    try:
                        dt = datetime.fromisoformat(start_str)
                        start_str = dt.strftime("%A, %B %d at %I:%M %p")
                    except:
                        pass
                
                title = event.get('title', 'Appointment')
                
                # Send SMS notification about the cancellation
                sms_status = ""
                if verify_phone:
                    try:
                        from backend.services.sms_service import send_sms
                        
                        sms_body = f"Hi {verify_name}, your appointment '{title}' on {start_str} has been cancelled."
                        
                        if send_sms(verify_phone, sms_body, self.workspace_id):
                            sms_status = " SMS cancellation sent."
                    except Exception as e:
                        sms_status = f" SMS error: {str(e)}"
                
                return f"Appointment '{title}' on {start_str} has been successfully cancelled.{sms_status}"
            else:
                with open("debug_calendar.log", "a") as f:
                    f.write(f"[{datetime.now()}] Failed to cancel appointment '{appointment_id}'\n")
                return f"Failed to cancel appointment {appointment_id}."
        except Exception as e:
            return f"Error cancelling appointment: {str(e)}"
        finally:
            db.close()



    @llm.function_tool(
        description="Dispatch a browser automation task to an OpenClaw worker. Use this for complex web research, filling forms, or interacting with websites.",
    )
    async def dispatch_to_openclaw(self, task_description: str, start_url: str = None):
        """
        Dispatch a task to OpenClaw.
        Args:
            task_description: Detailed description of what the browser worker should do.
            start_url: Optional starting URL.
        """
        from backend.database import SessionLocal
        from backend.models_db import Agent, Integration
        from backend.services.worker_service import WorkerService
        import json

        db = SessionLocal()
        try:
            # 1. Get Agent Settings for Instance ID
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if not agent:
                return "Error: Agent configuration not found."

            settings = agent.settings or {}
            
            # Check permissions
            allowed = agent.allowed_worker_types or []
            if "openclaw" not in allowed:
                return "Error: This agent is not authorized to use OpenClaw workers."

            # Get Instance ID
            # Priority: settings > stored in agent model directly (if added there) > default first instance
            instance_id = settings.get("open_claw_instance_id") or settings.get("openClawInstanceId")
            
            # If no specific instance bound, try to find a default one from Integrations
            if not instance_id:
                integration = db.query(Integration).filter(
                    Integration.workspace_id == self.workspace_id,
                    Integration.provider == "openclaw",
                    Integration.is_active == True
                ).first()
                
                if integration and integration.settings:
                    try:
                        data = json.loads(integration.settings)
                        instances = data.get("instances", [])
                        if instances:
                            instance_id = instances[0]["id"]
                    except:
                        pass
            
            if not instance_id:
                return "Error: No OpenClaw worker instance configured for this agent or workspace."

            # 2. Create Task
            service = WorkerService(db)
            
            input_data = {
                "goal": task_description,
                "url": start_url,
                "instance_id": instance_id
            }
            
            # mapped to 'openclaw' worker type in registry
            task = service.create_task(
                workspace_id=self.workspace_id, 
                worker_type="openclaw", 
                input_data=input_data, 
                dispatched_by_agent_id=self.agent_id
            )
            
            return f"Browser task started (ID: {task.id}). I will let you know when it is finished."

        except Exception as e:
            return f"Error dispatching to OpenClaw: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Edit an existing appointment. REQUIRES identity verification - you must ask for and provide the user's full name, phone number, and email address.",
    )
    async def edit_appointment(self, appointment_id: str, verify_name: str, verify_phone: str, verify_email: str, new_start_time: str = None, new_duration_minutes: int = None, new_title: str = None, new_description: str = None):
        """
        Edit an existing appointment.
        REQUIRES IDENTITY VERIFICATION: You must provide the user's name, phone, and email to verify their identity.
        Args:
            appointment_id: ID of the appointment to edit
            verify_name: User's full name (REQUIRED for security)
            verify_phone: User's phone number (REQUIRED for security)
            verify_email: User's email address (REQUIRED for security)
            new_start_time: New start time in ISO format (optional)
            new_duration_minutes: New duration in minutes (optional)
            new_title: New title (optional)
            new_description: New description (optional)
        """
        # SECURITY: Require identity verification
        if not verify_name or not verify_phone or not verify_email:
            return "ERROR: Identity verification required. Please ask the user for their Full Name, Phone Number, and Email Address before editing appointments."

        from backend.database import SessionLocal
        from backend.services.calendar_service import CalendarService
        from datetime import datetime, timedelta

        db = SessionLocal()
        try:
            service = CalendarService(db)
            
            # 1. Resolve Appointment ID (Local -> Google/External)
            # The agent might use the Local ID, but CalendarService needs the External ID (e.g. Google Event ID)
            from backend.models_db import Appointment
            from sqlalchemy import or_
            
            clean_id = appointment_id.strip()
            
            local_appt = db.query(Appointment).filter(
                Appointment.workspace_id == self.workspace_id,
                or_(Appointment.id == clean_id, Appointment.calendar_event_id == clean_id)
            ).first()
            
            resolved_event_id = clean_id
            if local_appt and local_appt.calendar_event_id:
                resolved_event_id = local_appt.calendar_event_id
                print(f"DEBUG: Resolved Local ID {clean_id} to External ID {resolved_event_id}")
            
            # 2. Fetch event using resolved ID
            event = service.get_event(self.workspace_id, resolved_event_id)
            if not event:
                 # Fallback: if resolution failed or not found, try original ID just in case
                 if resolved_event_id != clean_id:
                     event = service.get_event(self.workspace_id, clean_id)
                 
                 if not event:
                    return "Appointment not found."
            
            # 3. Verify Identity
            is_verified, message = service.verify_appointment_ownership(event, verify_name, verify_phone, verify_email)
            if not is_verified:
                return f"SECURITY WARNING: {message}"
            
            # --- Link Communication to Real Customer on Verification ---
            if self.communication_id and verify_email:
                try:
                     from backend.models_db import Customer, Communication
                     from sqlalchemy import func
                     
                     # Find the customer by verified email
                     customer = db.query(Customer).filter(
                         Customer.workspace_id == self.workspace_id,
                         func.lower(Customer.email) == verify_email.lower()
                     ).first()
                     
                     if customer:
                         comm_record = db.query(Communication).filter(Communication.id == self.communication_id).first()
                         if comm_record and comm_record.customer_id != customer.id:
                             print(f"DEBUG: Linking Communication {self.communication_id} to Customer {customer.id} (Edit)")
                             comm_record.customer_id = customer.id
                             # Also update session customer_id?
                             self.customer_id = customer.id
                             db.commit()
                except Exception as e:
                    print(f"Error linking communication in edit: {e}")
            # -----------------------------------------------------------
            
            # 4. Calculate new times if needed
            start_dt = None
            end_dt = None
            
            if new_start_time:
                try:
                    # ZONE FIX: Force input time to be interpreted as America/Toronto
                    from zoneinfo import ZoneInfo
                    tz = ZoneInfo("America/Toronto")
                    start_dt = datetime.fromisoformat(new_start_time)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=tz)
                    else:
                        start_dt = start_dt.astimezone(tz)
                except Exception as e:
                    return f"Error parsing new date/time: {e}"
                
                # Determine duration
                if new_duration_minutes:
                    duration = new_duration_minutes
                else:
                    # Calculate existing duration
                    old_start = datetime.fromisoformat(event['start']) if isinstance(event['start'], str) else event['start']
                    old_end = datetime.fromisoformat(event['end']) if isinstance(event['end'], str) else event['end']
                    # Calculate duration in minutes (fix simple subtraction)
                    duration = (old_end - old_start).total_seconds() / 60
                
                end_dt = start_dt + timedelta(minutes=duration)
            
            # 4. Update
            updated_event = service.update_event(
                self.workspace_id, 
                resolved_event_id, 
                start_time=start_dt, 
                end_time=end_dt, 
                title=new_title, 
                description=new_description
            )
            
            # Sync local DB
            from sqlalchemy import or_
            local_appt = db.query(Appointment).filter(
                Appointment.workspace_id == self.workspace_id,
                or_(Appointment.id == clean_id, Appointment.calendar_event_id == clean_id)
            ).first()
            
            if local_appt:
                if start_dt:
                    local_appt.appointment_date = start_dt
                if end_dt and start_dt:
                    duration = (end_dt - start_dt).total_seconds() / 60
                    local_appt.duration_minutes = duration
                if new_title:
                    local_appt.title = new_title
                if new_description:
                    local_appt.description = new_description
                local_appt.calendar_event_id = updated_event['id'] # Ensure synced
                db.commit()
            else:
                 # Fallback Search
                 fallback_appt = db.query(Appointment).filter(
                    Appointment.workspace_id == self.workspace_id,
                    Appointment.calendar_event_id == resolved_event_id
                ).first()
                 if fallback_appt:
                    print(f"DEBUG: Updating fallback appointment {fallback_appt.id} found via calendar_event_id {resolved_event_id}")
                    if start_dt:
                        fallback_appt.appointment_date = start_dt
                    if end_dt and start_dt:
                        duration = (end_dt - start_dt).total_seconds() / 60
                        fallback_appt.duration_minutes = duration
                    if new_title:
                        fallback_appt.title = new_title
                    if new_description:
                        fallback_appt.description = new_description
                    fallback_appt.calendar_event_id = updated_event['id']
                    db.commit()
                 else:
                    print(f"DEBUG: Failed to find local appointment to update for ID {clean_id} / {resolved_event_id}")
            
            # Format output
            start_str = updated_event.get('start')
            if isinstance(start_str, str):
                try:
                    dt = datetime.fromisoformat(start_str)
                    start_str = dt.strftime("%A, %B %d at %I:%M %p")
                except:
                    pass
            
            # Send SMS notification about the change
            sms_status = ""
            if verify_phone:
                try:
                    from backend.services.sms_service import send_sms
                    
                    title = updated_event.get('title', 'Your appointment')
                    sms_body = f"Hi {verify_name}, your appointment '{title}' has been updated and is now scheduled for {start_str}."
                    
                    if send_sms(verify_phone, sms_body):
                        sms_status = " SMS notification sent."
                except Exception as e:
                    sms_status = f" SMS error: {str(e)}"
            
            return f"Appointment updated successfully: '{updated_event['title']}' is now scheduled for {start_str}.{sms_status}"
        except Exception as e:
            import traceback
            error_msg = f"Error editing appointment: {str(e)}"
            print(f"ERROR in edit_appointment: {error_msg}\n{traceback.format_exc()}")
            return error_msg
        finally:
            db.close()


    @llm.function_tool(
        description="Check if a customer is already registered by their email or phone number. Use this BEFORE asking for name if the user implies they are an existing customer.",
    )
    async def check_registration_status(self, email: str = None, phone: str = None):
        """
        Check registration status.
        Args:
            email: Email to check
            phone: Phone to check
        """
        from backend.tools.customer_tools import CustomerTools
        # We don't have comm_id easily here in AgentTools instance unless passed to init. 
        # But we can pass None, it just won't link the comm automatically (which is fine, the voice agent log logic handles linking if we find an ID).
        
        # Actually, AgentTools is init with customer_id.
        tools = CustomerTools(workspace_id=self.workspace_id)
        return tools.check_registration_status(email, phone)

    @llm.function_tool(
        description="Register a new customer. Use this only after confirming they are NOT already registered.",
    )
    async def register_customer(self, first_name: str, last_name: str, phone: str = None, email: str = None):
        """
        Register a new customer.
        Args:
            first_name: First Name
            last_name: Last Name
            phone: Phone
            email: Email
        """
        from backend.tools.customer_tools import CustomerTools
        tools = CustomerTools(workspace_id=self.workspace_id)
        # Note: Voice Agent might not have comm_id linked here easily to update the log immediately, 
        # but the session will pick it up on next turn if we updated the customer_id in the tool.
        # Wait, the tool in CustomerTools updates `comm`. 
        # But `AgentTools` doesn't know the current `comm_id`.


    @llm.function_tool(
        description="Search for customers in the CRM by name, email, or other identifiers.",
    )
    async def search_customers(self, query: str):
        """
        Search for customers in the CRM.
        Args:
            query: The search term (name, email, etc.)
        """
        from backend.services.crm_service import CRMService
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            crm = CRMService(db)
            customers_data = crm.get_customers(workspace_id=self.workspace_id, search=query)
            customers = customers_data.get("items", [])
            if not customers:
                return f"No customers found matching '{query}'."
            
            # Format results
            lines = []
            for c in customers:
                name = f"{c.first_name or ''} {c.last_name or ''}".strip() or "Unnamed Customer"
                stage = (c.lifecycle_stage or "Lead")
                lines.append(f"- {name} ({c.email or 'No email'}) [ID: {c.id}, Stage: {stage}]")
            
            return "Found the following customers:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching customers: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Update an existing customer record. Use this to change contact info, lifecycle stage, or status.",
    )
    async def update_customer_record(
        self, 
        customer_id: str, 
        first_name: str = None, 
        last_name: str = None, 
        email: str = None, 
        phone: str = None, 
        company_name: str = None, 
        lifecycle_stage: str = None, 
        crm_status: str = None, 
        status: str = None
    ):
        """
        Update a customer record with new information.
        Args:
            customer_id: The ID of the customer to update.
            first_name: New first name.
            last_name: New last name.
            email: New email address.
            phone: New phone number.
            company_name: New company name.
            lifecycle_stage: New lifecycle stage (e.g., Subscriber, Lead, MQL, SQL, Opportunity, Customer).
            crm_status: New CRM status (e.g., New/Raw, Attempted to Contact, Working).
            status: New account status (e.g., active, trialing, churned).
        """
        from backend.database import SessionLocal
        from backend.models_db import Customer
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id, Customer.workspace_id == self.workspace_id).first()
            if not customer:
                return f"Customer {customer_id} not found."
            
            updates = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "company_name": company_name,
                "lifecycle_stage": lifecycle_stage,
                "crm_status": crm_status,
                "status": status
            }
            
            updated_fields = []
            for key, value in updates.items():
                if value is not None:
                    if hasattr(customer, key):
                        setattr(customer, key, value)
                        updated_fields.append(key)
            
            if not updated_fields:
                return "No updates provided."
            
            db.commit()
            return f"Successfully updated customer {customer_id}. Fields: {', '.join(updated_fields)}"

        except Exception as e:
            db.rollback()
            return f"Error updating customer: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="List active sales deals or leads in the pipeline.",
    )
    async def list_deals(self, stage: str = None):
        """
        List deals in the sales pipeline.
        Args:
            stage: Optional filter by stage (e.g., 'lead', 'qualified', 'closed_won').
        """
        from backend.database import SessionLocal
        from backend.models_db import Deal
        db = SessionLocal()
        try:
            query = db.query(Deal).filter(Deal.workspace_id == self.workspace_id)
            if stage:
                query = query.filter(Deal.stage == stage)
            
            deals = query.order_by(Deal.created_at.desc()).limit(20).all()
            if not deals:
                return "No deals found."
            
            lines = []
            for d in deals:
                val = f"${d.value/100:.2f}" if d.value else "N/A"
                lines.append(f"- {d.title}: {val} (Stage: {d.stage}, ID: {d.id})")
            
            return "Active Deals:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing deals: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Create a new sales deal or update an existing one.",
    )
    async def create_or_update_deal(self, title: str, customer_id: str = None, value_cents: int = None, stage: str = "lead", deal_id: str = None):
        """
        Create or update a deal.
        Args:
            title: Title for the deal.
            customer_id: ID of the customer this deal belongs to.
            value_cents: Value of the deal in cents.
            stage: Stage of the deal.
            deal_id: If provided, updates existing deal instead of creating new.
        """
        from backend.database import SessionLocal
        from backend.models_db import Deal
        from uuid import uuid4
        db = SessionLocal()
        try:
            if deal_id:
                deal = db.query(Deal).filter(Deal.id == deal_id, Deal.workspace_id == self.workspace_id).first()
                if not deal:
                    return f"Deal {deal_id} not found."
            else:
                deal = Deal(id=f"deal_{str(uuid4())[:8]}", workspace_id=self.workspace_id)
                db.add(deal)
            
            deal.title = title
            if customer_id: deal.customer_id = customer_id
            if value_cents is not None: deal.value = value_cents
            deal.stage = stage
            
            db.commit()
            return f"Deal '{title}' {'updated' if deal_id else 'created'} successfully (ID: {deal.id})."
        except Exception as e:
            db.rollback()
            return f"Error managing deal: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="List active marketing campaigns (e.g., Appointment Reminders, Lead Nurture).",
    )
    async def list_active_campaigns(self):
        """List active campaigns for this workspace."""
        from backend.database import SessionLocal
        from backend.models_db import Campaign
        db = SessionLocal()
        try:
            campaigns = db.query(Campaign).filter(Campaign.workspace_id == self.workspace_id, Campaign.status == "active").all()
            if not campaigns:
                return "No active campaigns found."
            
            lines = []
            for c in campaigns:
                lines.append(f"- {c.name} (Type: {c.trigger_type}, ID: {c.id})")
            
            return "Active Campaigns:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing campaigns: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="List specialized worker agents available for dispatch (e.g. Email Assistant, Job Search, etc.).",
    )
    async def list_worker_agents(self):
        """List all available worker agent templates."""
        from backend.services.worker_service import WorkerService
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            service = WorkerService(db)
            templates = service.get_all_templates(active_only=True)
            if not templates:
                return "No specialized worker agents available for dispatch."
            
            lines = []
            for t in templates:
                lines.append(f"- {t.name} (Slug: {t.slug}): {t.description}")
            
            return "Available Worker Agents:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing worker agents: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Check if Google Calendar integration is active and sync is healthy.",
    )
    async def check_google_calendar_sync(self):
        """Check the status of Google Calendar integration."""
        from backend.database import SessionLocal
        from backend.models_db import Integration
        db = SessionLocal()
        try:
            integration = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider == "google_calendar",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return "Google Calendar is not connected or is currently inactive."
            
            return "Google Calendar integration is ACTIVE and sync is healthy."
        except Exception as e:
            return f"Error checking calendar status: {str(e)}"
        finally:
            db.close()

    # --- MAILBOX TOOLS ---

    def _get_mailbox_service(self, provider: str, db):
        if provider == "gmail":
            from backend.services.gmail_service import GmailService
            return GmailService(db)
        elif provider == "outlook":
            from backend.services.outlook_service import OutlookService
            return OutlookService(db)
        elif provider == "icloud":
            from backend.services.icloud_service import ICloudService
            return ICloudService(db)
        else:
            raise ValueError(f"Unknown mailbox provider: {provider}. Supported: gmail, outlook, icloud")

    @llm.function_tool(
        description="List recent emails from a connected mailbox (gmail, outlook, or icloud).",
    )
    async def list_inbox_emails(self, provider: str, limit: int = 5):
        """
        List recent emails.
        Args:
            provider: 'gmail', 'outlook', or 'icloud'
            limit: Number of emails to retrieve (default 5)
        """
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            service = self._get_mailbox_service(provider, db)
            emails = service.list_emails(self.workspace_id, limit)
            if not emails:
                return f"No emails found in {provider} inbox."
            
            # Format nicely
            output = [f"Inbox ({provider}):"]
            for email in emails:
                output.append(f"- [{email['id']}] {email['date']} | From: {email['from']} | Subject: {email['subject']}")
            return "\n".join(output)
        except Exception as e:
            return f"Error listing emails: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Read the content of a specific email by ID.",
    )
    async def read_email(self, provider: str, email_id: str):
        """
        Read full content of an email.
        Args:
            provider: 'gmail', 'outlook', or 'icloud'
            email_id: The ID of the email to read
        """
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            service = self._get_mailbox_service(provider, db)
            email_data = service.read_email(self.workspace_id, email_id)
            
            return f"""
Subject: {email_data.get('subject')}
From: {email_data.get('from')}
To: {email_data.get('to')}
Date: {email_data.get('date')}

{email_data.get('body')}
"""
        except Exception as e:
            return f"Error reading email: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Search emails in a mailbox.",
    )
    async def search_emails(self, provider: str, query: str):
        """
        Search for emails.
        Args:
            provider: 'gmail', 'outlook', or 'icloud'
            query: Search terms (e.g. "invoice", "from:john")
        """
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            service = self._get_mailbox_service(provider, db)
            emails = service.search_emails(self.workspace_id, query)
            if not emails:
                return f"No emails found matching '{query}' in {provider}."
            
            output = [f"Search Results ({provider}):"]
            for email in emails:
                output.append(f"- [{email['id']}] {email['date']} | From: {email['from']} | Subject: {email['subject']}")
            return "\n".join(output)
        except Exception as e:
            return f"Error searching emails: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Send an email via a connected mailbox.",
    )
    async def send_email_via_mailbox(self, provider: str, to: str, subject: str, body: str):
        """
        Send an email.
        Args:
            provider: 'gmail', 'outlook', or 'icloud'
            to: Recipient email address
            subject: Email subject
            body: Email body content
        """
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            service = self._get_mailbox_service(provider, db)
            service.send_email(self.workspace_id, to, subject, body)
            return f"Email sent successfully to {to} via {provider}."
        except Exception as e:
            return f"Error sending email: {str(e)}"
        finally:
            db.close()

    # --- DRIVE TOOLS ---

    @llm.function_tool(
        description="List files in Google Drive. Can optionally specify a folder ID.",
    )
    async def list_drive_files(self, folder_id: str = None, limit: int = 10):
        """
        List files in Google Drive.
        Args:
            folder_id: Optional folder ID to list contents of
            limit: Max files to return
        """
        from backend.database import SessionLocal
        from backend.services.google_drive_service import GoogleDriveService
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            files = service.list_files(self.workspace_id, folder_id, limit)
            if not files:
                return "No files found."
            
            output = ["Google Drive Files:"]
            for f in files:
                output.append(f"- [{f['id']}] {f['name']} ({f.get('mimeType')}) - {f.get('link')}")
            return "\n".join(output)
        except Exception as e:
            return f"Error listing Drive files: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Read content of a file from Google Drive (text/document based).",
    )
    async def read_drive_file(self, file_id: str):
        """
        Read a file's content from Google Drive.
        Args:
            file_id: ID of the file
        """
        from backend.database import SessionLocal
        from backend.services.google_drive_service import GoogleDriveService
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            content = service.read_file(self.workspace_id, file_id)
            return f"File Content:\n\n{content}"
        except Exception as e:
            return f"Error reading Drive file: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Upload a text-based file to Google Drive.",
    )
    async def upload_drive_file(self, name: str, content: str):
        """
        Upload a new file to Google Drive.
        Args:
            name: Filename (e.g. "notes.txt")
            content: File content
        """
        from backend.database import SessionLocal
        from backend.services.google_drive_service import GoogleDriveService
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            result = service.upload_file(self.workspace_id, name, content)
            return f"File uploaded successfully: {result['link']}"
        except Exception as e:
            return f"Error uploading file: {str(e)}"
        finally:
            db.close()

    @llm.function_tool(
        description="Search for files in Google Drive.",
    )
    async def search_drive_files(self, query: str):
        """
        Search Google Drive files by name.
        Args:
            query: Name query
        """
        from backend.database import SessionLocal
        from backend.services.google_drive_service import GoogleDriveService
        db = SessionLocal()
        try:
            service = GoogleDriveService(db)
            files = service.search_files(self.workspace_id, query)
            if not files:
                return f"No files found matching '{query}'."
            
            output = [f"Search Results for '{query}':"]
            for f in files:
                output.append(f"- [{f['id']}] {f['name']} - {f.get('link')}")
            return "\n".join(output)
        except Exception as e:
            return f"Error searching Drive files: {str(e)}"
        finally:
            db.close()


    # =========================================================================
    # WORKER DISPATCH TOOLS
    # =========================================================================

    @llm.function_tool(
        description="List available autonomous workers that can perform extended tasks like research, content generation, or data gathering.",
    )
    async def list_available_workers(self):
        """
        List all available worker types. Use this to help the user choose a worker.
        Returns list of workers with name, description, and category.
        """
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        
        db = SessionLocal()
        try:
            service = WorkerService(db)
            templates = service.get_all_templates()
            
            if not templates:
                return "No workers are currently available."
            
            result = "Available Workers:\n"
            for t in templates:
                result += f"\n• {t.name} ({t.slug})\n  {t.description}\n"
            
            return result
        finally:
            db.close()

    @llm.function_tool(
        description="Get the required parameters for a worker type. Use this BEFORE dispatching to know what information to collect.",
    )
    async def get_worker_schema(self, worker_type: str):
        """
        Get the parameter schema for a worker type.
        Args:
            worker_type: The worker slug (e.g., 'job-search', 'lead-research', 'content-writer')
        """
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        import json
        
        db = SessionLocal()
        try:
            service = WorkerService(db)
            schema = service.get_template_schema(worker_type)
            
            if not schema:
                return f"Worker type '{worker_type}' not found. Use list_available_workers to see options."
            
            # Format schema for LLM
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            result = f"Parameters for {worker_type}:\n\n"
            for name, prop in properties.items():
                req = "(REQUIRED)" if name in required else "(optional)"
                title = prop.get("title", name)
                desc = prop.get("description", "")
                default = prop.get("default", "")
                type_info = prop.get("type", "")
                
                result += f"• {title} {req}\n"
                if desc:
                    result += f"  {desc}\n"
                if default:
                    result += f"  Default: {default}\n"
                result += "\n"
            
            return result
        finally:
            db.close()

    # schedule_background_task REMOVED to force synchronous execution via run_task_now



    @llm.function_tool(
        description="Execute a task IMMEDIATELY and return the result. Use this for ALL normal requests (Weather, Flights, Job Search, Research, Email, etc.) where the user wants an answer now.",
    )
    async def run_task_now(self, worker_type: str, input_data: str):
        """
        Execute a worker synchronously and get the result immediately.
        
        Args:
            worker_type: The worker slug. Options:
                - 'weather-worker': {"location": "City, State"}
                - 'flight-tracker': {"flight_number": "AC123"} OR {"origin": "JFK", "destination": "LHR", "airline": "BA"}
                - 'job-search': {"job_title": "Role", "location": "City", "job_type": "full-time"}
                - 'map-worker': {"origin": "A", "destination": "B", "mode": "driving"}
            input_data: Valid JSON string of parameters.
        """
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        import json
        
        # --- Worker Registry ---
        def get_worker_handler(w_type: str):
            # Utility
            if w_type == "weather-worker":
                from backend.workers.weather_worker import WeatherWorker
                return WeatherWorker.run
            elif w_type == "flight-tracker":
                from backend.workers.flight_tracker_worker import FlightTrackerWorker
                return FlightTrackerWorker.run 
            elif w_type == "map-worker":
                from backend.workers.map_worker import MapWorker
                return MapWorker.run
            # Core
            elif w_type == "job-search":
                from backend.workers.job_search_worker import JobSearchWorker
                return JobSearchWorker.execute 
            elif w_type == "lead-research":
                from backend.workers.lead_research_worker import LeadResearchWorker
                return LeadResearchWorker.execute
            elif w_type == "content-writer":
                from backend.workers.content_writer_worker import ContentWriterWorker
                return ContentWriterWorker.execute
            elif w_type == "email-worker":
                from backend.workers.email_worker import EmailWorker
                return EmailWorker.execute
            elif w_type == "sales-outreach":
                from backend.workers.sales_outreach_worker import SalesOutreachWorker
                return SalesOutreachWorker.run 
            elif w_type == "faq-resolution":
                from backend.workers.faq_resolution_worker import FAQResolutionWorker
                return FAQResolutionWorker.run
            elif w_type == "meeting-coordination":
                from backend.workers.meeting_coordination_worker import MeetingCoordinationWorker
                return MeetingCoordinationWorker.run
            elif w_type == "order-status":
                from backend.workers.order_status_worker import OrderStatusWorker
                return OrderStatusWorker.run
            elif w_type == "hr-onboarding":
                from backend.workers.hr_onboarding_worker import HROnboardingWorker
                return HROnboardingWorker.run
            elif w_type == "payment-billing":
                from backend.workers.payment_billing_worker import PaymentBillingWorker
                return PaymentBillingWorker.run
            elif w_type == "it-support":
                from backend.workers.it_support_worker import ITSupportWorker
                return ITSupportWorker.run
            elif w_type == "intelligent-routing":
                from backend.workers.intelligent_routing_worker import IntelligentRoutingWorker
                return IntelligentRoutingWorker.run
            elif w_type == "data-entry":
                from backend.workers.data_entry_worker import DataEntryWorker
                return DataEntryWorker.run
            elif w_type == "document-processing":
                from backend.workers.document_processing_worker import DocumentProcessingWorker
                return DocumentProcessingWorker.run
            elif w_type == "content-moderation":
                from backend.workers.content_moderation_worker import ContentModerationWorker
                return ContentModerationWorker.run
            elif w_type == "sentiment-escalation":
                from backend.workers.sentiment_escalation_worker import SentimentEscalationWorker
                return SentimentEscalationWorker.run
            elif w_type == "translation-localization":
                from backend.workers.translation_worker import TranslationWorker
                return TranslationWorker.run
            elif w_type == "compliance-risk":
                from backend.workers.compliance_worker import ComplianceWorker
                return ComplianceWorker.run
            elif w_type == "sms-messaging":
                from backend.workers.sms_messaging_worker import SMSMessagingWorker
                return SMSMessagingWorker.run
            elif w_type == "openclaw":
                from backend.workers.openclaw_worker import OpenClawWorker
                return OpenClawWorker.run
            
            return None

        db = SessionLocal()
        try:
            service = WorkerService(db)
            
            # Parse input
            try:
                params = json.loads(input_data)
            except:
                return "Error: input_data must be valid JSON string"

            # Create Task Record
            task = service.create_task(
                workspace_id=self.workspace_id,
                worker_type=worker_type,
                input_data=params,
                customer_id=self.customer_id,
                dispatched_by_agent_id=self.agent_id
            )
            
            # Get Handler
            handler = get_worker_handler(worker_type)
            if not handler:
                service.fail_task(task.id, f"Unknown worker type: {worker_type}")
                return f"Error: Unknown worker type {worker_type}"
            
            # Execute Sync (Thread-Safe Wrapper)
            service.update_task_status(task.id, "running", current_step="Executing synchronously...", steps_completed=1, steps_total=5)
            
            import asyncio
            import functools
            loop = asyncio.get_running_loop()
            
            try:
                # Wrap the blocking call in a thread
                handler_func = functools.partial(handler, task.id, params, service, db)
                result = await loop.run_in_executor(None, handler_func)
                
                # Check for explicit error dict
                if isinstance(result, dict) and "error" in result:
                    service.fail_task(task.id, result["error"])
                    return f"Worker Error: {result['error']}"
                
                # Success
                service.complete_task(task.id, result, tokens_used=0)
                service.update_task_status(task.id, "completed", current_step="Done", steps_completed=1, steps_total=1)
                
                # Return Summary
                if isinstance(result, dict):
                    if "weather_info" in result: return str(result["weather_info"])
                    if "flight_status" in result: return str(result["flight_status"])
                    if "route_info" in result: return str(result["route_info"])
                    if "summary" in result: return str(result["summary"])
                    if "jobs_found" in result: return f"Found {len(result['jobs_found'])} jobs. Top: {result['jobs_found'][0].get('title')}"
                
                return str(result)
                
            except Exception as e:
                service.fail_task(task.id, str(e))
                print(f"Worker Sync Exec Error: {e}")
                import traceback
                traceback.print_exc()
                return f"Execution Error: {str(e)}"
                
        finally:
            db.close()

    @llm.function_tool(
        description="Check the status of a previously dispatched worker task.",
    )
    async def check_agent_task_status(self, task_id: str):
        """
        Check the status of a worker task.
        Args:
            task_id: The task ID returned from dispatch_worker_task
        """
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        import json
        
        db = SessionLocal()
        try:
            service = WorkerService(db)
            task = service.get_task(task_id)
            
            if not task:
                return f"Task '{task_id}' not found."
            
            result = f"Task Status: {task.status.upper()}\n"
            
            if task.steps_total:
                result += f"Progress: {task.steps_completed}/{task.steps_total}\n"
            
            if task.current_step:
                result += f"Current Step: {task.current_step}\n"
            
            if task.status == "completed" and task.output_data:
                result += f"\nResults:\n"
                # Format output nicely
                if isinstance(task.output_data, dict):
                    if "summary" in task.output_data:
                        result += task.output_data["summary"]
                    if "jobs_found" in task.output_data:
                        jobs = task.output_data["jobs_found"][:5]  # Top 5
                        result += f"\n\nTop {len(jobs)} Results:\n"
                        for i, job in enumerate(jobs, 1):
                            result += f"\n{i}. {job.get('title', 'Unknown')}\n   {job.get('url', '')}\n"
                else:
                    result += str(task.output_data)
            
            if task.status == "failed" and task.error_message:
                result += f"\nError: {task.error_message}"
            
            return result
        finally:
            db.close()

    @llm.function_tool(
        description="Send an SMS text message to a customer. Use this to send notifications, reminders, or follow-ups.",
    )
    async def send_sms_notification(self, phone_number: str, message: str):
        """
        Send an SMS notification to a customer.
        Args:
            phone_number: The recipient's phone number (any format accepted)
            message: The message body to send (max 1600 characters)
        """
        if not phone_number:
            return "Error: Phone number is required."
        
        if not message:
            return "Error: Message body is required."
        
        if len(message) > 1600:
            return "Error: Message is too long. Maximum 1600 characters allowed."
        
        try:
            from backend.services.sms_service import send_sms
            
            success, error = send_sms(phone_number, message, self.workspace_id)
            
            if success:
                return f"SMS sent successfully to {phone_number}."
            else:
                return f"Failed to send SMS: {error}"
        except Exception as e:
            return f"Error sending SMS: {str(e)}"

    @llm.function_tool(
        description="Send an email notification to a customer. Use this to send confirmations, updates, or information.",
    )
    async def send_email_notification(self, email_address: str, subject: str, message: str):
        """
        Send an email notification to a customer.
        Args:
            email_address: The recipient's email address
            subject: Email subject line
            message: The message body (can include basic HTML formatting)
        """
        if not email_address or "@" not in email_address:
            return "Error: Valid email address is required."
        
        if not subject:
            return "Error: Email subject is required."
        
        if not message:
            return "Error: Email message body is required."
        
        try:
            from backend.services.email_service import EmailService
            
            email_service = EmailService()
            
            # Wrap plain text in basic HTML if no tags detected
            html_content = message
            if "<" not in message:
                html_content = f"<p>{message.replace(chr(10), '<br>')}</p>"
            
            success, error = email_service.send_email(
                to_email=email_address,
                subject=subject,
                html_content=html_content,
                workspace_id=self.workspace_id
            )
            
            if success:
                return f"Email sent successfully to {email_address}."
            else:
                return f"Failed to send email: {error}"
        except Exception as e:
            return f"Error sending email: {str(e)}"

    @llm.function_tool(
        description="Execute ANY autonomous worker (Research, Content, Email, Weather, etc.) synchronously. Use this to perform the task and get the result IMMEDIATELY.",
    )
    async def execute_worker_sync(self, worker_type: str, input_data: str):
        """
        Execute a worker synchronously and get the result immediately.
        Args:
            worker_type: The worker slug (e.g. 'job-search', 'weather-worker', 'email-worker')
            input_data: JSON string of parameters
        """
        from backend.database import SessionLocal
        from backend.services.worker_service import WorkerService
        import json
        
        # Use Global Registry
        # Logic moved to top-level get_worker_handler
        pass

        db = SessionLocal()
        try:
            service = WorkerService(db)
            
            # Parse input
            try:
                params = json.loads(input_data)
            except:
                return "Error: input_data must be valid JSON string"

            # Create Task Record
            task = service.create_task(
                workspace_id=self.workspace_id,
                worker_type=worker_type,
                input_data=params,
                customer_id=self.customer_id,
                dispatched_by_agent_id=self.agent_id
            )
            
            # Get Handler
            handler = get_worker_handler(worker_type)
            if not handler:
                service.fail_task(task.id, f"Unknown worker type: {worker_type}")
                return f"Error: Unknown worker type {worker_type}"
            
            # Execute Sync (Thread-Safe Wrapper)
            service.update_task_status(task.id, "running", current_step="Executing synchronously...", steps_completed=1, steps_total=5)
            
            import asyncio
            import functools
            loop = asyncio.get_running_loop()
            
            try:
                # Wrap the blocking call in a thread
                # This prevents 'asyncio.run() cannot be called from a running event loop' 
                # because the thread is separate from the main loop.
                handler_func = functools.partial(handler, task.id, params, service, db)
                result = await loop.run_in_executor(None, handler_func)
                
                # Check for explicit error dict
                if isinstance(result, dict) and "error" in result:
                    service.fail_task(task.id, result["error"])
                    return f"Worker Error: {result['error']}"
                
                # Success
                service.complete_task(task.id, result, tokens_used=0)
                service.update_task_status(task.id, "completed", current_step="Done", steps_completed=5, steps_total=5)
                
                # Return Summary
                if isinstance(result, dict):
                    if "weather_info" in result: return str(result["weather_info"])
                    if "flight_status" in result: return str(result["flight_status"])
                    if "route_info" in result: return str(result["route_info"])
                    if "summary" in result: return str(result["summary"])
                    if "jobs_found" in result: return f"Found {len(result['jobs_found'])} jobs. Top: {result['jobs_found'][0].get('title')}"
                
                return str(result)
                
            except Exception as e:
                service.fail_task(task.id, str(e))
                print(f"Worker Sync Exec Error: {e}")
                import traceback
                traceback.print_exc()
                return f"Execution Error: {str(e)}"
                
        finally:
            db.close()


