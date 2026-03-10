from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from datetime import datetime, timezone
import json
import os

from backend.models_db import Customer, Communication, Appointment, User
from backend.database import generate_customer_id, generate_guest_id

class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def get_customers(self, workspace_id: str, skip: int = 0, limit: int = 10, search: str = None):
        """Fetch paginated list of customers, excluding owner/admin users."""
        
        # Query customers for this workspace
        query = self.db.query(Customer).filter(
            Customer.workspace_id == workspace_id,
            Customer.status.notin_(['converted', 'deleted'])
        )
        
        if search:
            search_filt = f"%{search}%"
            query = query.filter(
                (Customer.first_name.ilike(search_filt)) | 
                (Customer.last_name.ilike(search_filt)) | 
                (Customer.email.ilike(search_filt))
            )
            
        total = query.count()
        query = query.order_by(desc(Customer.created_at))
        items = query.offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}

    def get_customer_by_id(self, workspace_id: str, customer_id: str):
        """Get a single customer by ID."""
        return self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id
        ).first()

    def create_customer(self, workspace_id: str, data: dict):
        """
        Create a new customer, OR update existing one if found (by phone/email).
        
        Identity Validation Rules:
        - If email exists + (name OR phone matches) → Update existing profile (same customer)
        - If email exists + (name AND phone don't match) → Reject (identity mismatch)
        """
        email = data.get("email")
        phone = data.get("phone")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        # 1. Look for EXISTING customer (Guest or Real)
        existing_customer = None
        found_by = None  # Track how we found the customer
        
        # A. Check by Phone (Strongest match - phone already validates identity)
        if phone:
            # Normalize phone for matching
            clean_phone = "".join(filter(str.isdigit, phone))
            phone_variations = [phone, clean_phone]
            if clean_phone:
                phone_variations.extend([f"+{clean_phone}", f"+1{clean_phone}"])
                if len(clean_phone) == 10:
                    phone_variations.append(f"1{clean_phone}")
                if len(clean_phone) == 11 and clean_phone.startswith("1"):
                    phone_variations.append(clean_phone[1:])
            
            existing_customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.phone.in_(phone_variations),
                Customer.status.notin_(['converted', 'deleted'])
            ).first()
            if existing_customer:
                found_by = "phone"
            
        # B. Check by Email (requires identity validation)
        if not existing_customer and email:
            existing_customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                func.lower(Customer.email) == email.lower().strip(),
                Customer.status.notin_(['converted', 'deleted'])
            ).first()
            if existing_customer:
                found_by = "email"

        # If found by EMAIL, validate identity before allowing update
        if existing_customer and found_by == "email":
            # Identity validation: at least name OR phone must match
            name_matches = False
            phone_matches = False
            
            # Check name match (case-insensitive)
            if first_name and last_name:
                existing_full_name = f"{existing_customer.first_name or ''} {existing_customer.last_name or ''}".lower().strip()
                provided_full_name = f"{first_name} {last_name}".lower().strip()
                name_matches = existing_full_name == provided_full_name
            elif first_name:
                name_matches = (existing_customer.first_name or "").lower() == first_name.lower()
            
            # Check phone match
            if phone and existing_customer.phone:
                clean_provided = "".join(filter(str.isdigit, phone))
                clean_existing = "".join(filter(str.isdigit, existing_customer.phone))
                phone_matches = clean_provided == clean_existing or clean_provided[-10:] == clean_existing[-10:]
            
            # If neither name nor phone matches, reject the request
            if not name_matches and not phone_matches:
                raise ValueError(
                    f"Identity mismatch: A customer profile already exists with email '{email}' "
                    f"but the provided name and phone number do not match. "
                    f"Please verify the customer's identity or use a different email."
                )
            
        # If found (and validated if by email), UPDATE and RETURN
        if existing_customer:
            if first_name: existing_customer.first_name = first_name
            if last_name: existing_customer.last_name = last_name
            if email: existing_customer.email = email
            # Phone is likely same, but update if different (e.g. found by email)
            if phone: existing_customer.phone = phone
            
            # Update other fields if provided
            if data.get("plan"): existing_customer.plan = data.get("plan")
            if data.get("lifecycle_stage"): existing_customer.lifecycle_stage = data.get("lifecycle_stage")
            if data.get("crm_status"): existing_customer.crm_status = data.get("crm_status")
            
            self.db.commit()
            self.db.refresh(existing_customer)
            return existing_customer

        # 2. If NOT found, Create New
        customer = Customer(
            id=generate_customer_id(),
            workspace_id=workspace_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            status=data.get("status", "active"),
            plan=data.get("plan", "Starter"),
            usage_limit=data.get("usage_limit", 1000),
            usage_used=data.get("usage_used", 0),
            lifecycle_stage=data.get("lifecycle_stage"),
            crm_status=data.get("crm_status"),
            customer_type=data.get("customer_type")
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def convert_to_customer(self, customer_id: str, conversion_trigger: str):
        """
        Convert a Guest/Lead to a full Customer.
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # If already a customer, just return (idempotent)
        if customer.customer_type == "customer":
            return customer

        # Perform conversion
        if not customer.cust_id:
            customer.cust_id = generate_customer_id()
        
        customer.customer_type = "customer"
        customer.lifecycle_stage = "Customer"
        customer.crm_status = "Active"
        customer.converted_at = datetime.now(timezone.utc)
        customer.converted_by = conversion_trigger
        
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_status_on_appointment(self, workspace_id: str, customer_id: str):
        """
        Upgrade customer status when an appointment is booked.
        """
        try:
            self.convert_to_customer(
                customer_id=customer_id,
                conversion_trigger="appointment"
            )
            return True
        except Exception as e:
            # Log error ideally
            return False

    def get_or_create_from_identifier(self, workspace_id: str, identifier: str, channel: str = "phone", name: str = None) -> Customer:
        """
        Find or create a customer/guest.
        Lookup priority:
        1. Session ID (ann_...)
        2. Phone number (normalized)
        3. Email address
        """
        if not identifier:
            return None
            
        # 1. CHECK SESSION ID (Strongest for anonymous)
        if identifier.startswith("ann_"):
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.session_id == identifier,
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer
                
            # If not found but is session ID, create new guest linked to this session
            return self._create_guest(workspace_id, session_id=identifier, channel=channel, name=name)

        # 2. CLEAN IDENTIFIER FOR CONTACT LOOKUP
        clean_id = identifier.replace("sip:", "").replace("whatsapp:", "").strip()
        is_email = "@" in clean_id
        
        if is_email:
            clean_id = clean_id.lower()
            
            # Check Email
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                func.lower(Customer.email) == clean_id,
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer
                
        else:
            # Check Phone (with normalization)
            digits_only = "".join(filter(str.isdigit, clean_id))
            search_values = {clean_id}
            if digits_only:
                search_values.add(digits_only)
                search_values.add(f"+{digits_only}")
                if len(digits_only) == 10:
                    search_values.add(f"1{digits_only}")
                if len(digits_only) == 11 and digits_only.startswith("1"):
                    search_values.add(digits_only[1:])
            
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.phone.in_(search_values),
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer

        # 3. CREATE NEW GUEST (if no match)
        return self._create_guest(workspace_id, identifier_val=clean_id, is_email=is_email, channel=channel, name=name)

    def _create_guest(self, workspace_id: str, session_id: str = None, identifier_val: str = None, is_email: bool = False, channel: str = "web", name: str = None):
        guest_id = generate_guest_id()
        first_name = "Guest"
        last_name = "User"
        
        if name:
             parts = name.split(" ", 1)
             first_name = parts[0]
             if len(parts) > 1:
                 last_name = parts[1]
        
        guest = Customer(
            id=guest_id,
            workspace_id=workspace_id,
            first_name=first_name,
            last_name=last_name,
            status="active",
            customer_type="guest",
            session_id=session_id
        )
        
        if identifier_val:
            if is_email:
                guest.email = identifier_val
            else:
                guest.phone = identifier_val
                
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def ensure_customer_from_interaction(self, workspace_id: str, identifier: str, channel: str, name: str = None):
        """
        Ensure a customer record exists for the given identifier (email or phone).
        Delegates to get_or_create_from_identifier for resolution logic.
        Updates last_contact_date.
        """
        customer = self.get_or_create_from_identifier(workspace_id, identifier, channel, name)
        
        if customer:
            # Update last contact date
            customer.last_contact_date = datetime.now(timezone.utc)
            self.db.commit()
            
        return customer

    def analyze_and_update_customer_status(self, customer_id: str, interaction_text: str, interaction_type: str = "chat"):
        """
        Analyze an interaction using LLM to update customer CRM status and lifecycle stage.
        """
        # 1. Fetch Customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "error": "Customer not found"}

        # 2. Prepare Context (Current State)
        current_state = {
            "customer_type": customer.customer_type,
            "lifecycle_stage": customer.lifecycle_stage,
            "crm_status": customer.crm_status,
            "account_status": customer.status
        }
        
        # 3. Construct Prompt
        prompt = f"""
        You are an expert CRM manager. Analyze the following customer interaction and determine if the customer's classification should be updated.
        
        Current Customer State:
        {json.dumps(current_state, indent=2)}
        
        New Interaction ({interaction_type}):
        "{interaction_text}"
        
        Rules for Classification:
        1. Lifecycle Stage:
           - Subscriber: Just signed up, no interaction.
           - Lead: Engaged in chat, asked general questions.
           - MQL (Marketing Qualified Lead): Asked specific questions about features, pricing, or use cases.
           - SQL (Sales Qualified Lead): Requested a demo, quote, or meeting.
           - Opportunity: Appointment booked or negotiation started.
           - Customer: Completed purchase or payment.
           - Evangelist: Positive feedback, referrals.
           
        2. CRM Status (Interaction Status):
           - New/Raw: No contact yet.
           - Attempted to Contact: specific outreach made (outbound).
           - Working/Contacted: Active conversation.
           - Nurture: Interested but not ready (e.g., "ask me later").
           - Bad Fit: Explicitly not interested or wrong profile.
           - At Risk: Negative sentiment, complaints, "cancel" mentioned.
           - Active: Normal healthy interaction.
           
        3. Customer Type:
           - B2B: Mentions company, team, enterprise needs.
           - B2C: Personal use, individual email.
        
        Return ONLY a valid JSON object with keys: "lifecycle_stage", "crm_status", "customer_type". 
        If a field should NOT change from its current state (or if there is insufficient info to change it), set it to null.
        Do strictly adhere to the allowed values if possible (lowercase/snake_case preferred for db storage).
        """
        
        try:
            from backend.lib.ai_client import get_ai_client
            client, model_name = get_ai_client(async_mode=False)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a CRM AI assistant. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # 4. Apply Updates
            updates_made = False
            changes = {}
            
            # Helper to normalize and check changes
            def update_if_changed(field, new_val):
                current_val = getattr(customer, field)
                # Only update if new_val is not None/Empty and different from current
                if new_val and new_val.lower() != (current_val or "").lower():
                    setattr(customer, field, new_val.lower()) # Store as lowercase for consistency
                    return True
                return False

            if result.get("lifecycle_stage"):
                if update_if_changed("lifecycle_stage", result["lifecycle_stage"]):
                    changes["lifecycle_stage"] = result["lifecycle_stage"]
                    updates_made = True
            
            if result.get("crm_status"):
                if update_if_changed("crm_status", result["crm_status"]):
                    changes["crm_status"] = result["crm_status"]
                    updates_made = True
                
            if result.get("customer_type"):
                if update_if_changed("customer_type", result["customer_type"]):
                    changes["customer_type"] = result["customer_type"]
                    updates_made = True
            
            if updates_made:
                self.db.commit()
                self.db.refresh(customer)
                
            return {"success": True, "updates": changes, "changed": updates_made, "analysis": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

