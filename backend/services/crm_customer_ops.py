import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models_db import Customer
from backend.database import generate_customer_id, generate_guest_id, format_session_id
from datetime import datetime, timezone

logger = logging.getLogger("crm-customer-ops")

class CRMCustomerOps:
    @staticmethod
    def get_or_create_from_identifier(db: Session, workspace_id: str, identifier: str, channel: str = "phone", name: str = None) -> Customer:
        if not identifier: return None
            
        # 1. Session ID Check
        if identifier.startswith("ann_"):
            customer = db.query(Customer).filter(Customer.workspace_id == workspace_id, Customer.session_id == identifier, Customer.status != "deleted").first()
            if customer: return customer
            return CRMCustomerOps._create_guest(db, workspace_id, session_id=identifier, channel=channel, name=name)

        # 2. Identifier Lookup (Email or Phone)
        clean_id = identifier.replace("sip:", "").replace("whatsapp:", "").strip()
        is_email = "@" in clean_id
        
        if is_email:
            clean_id = clean_id.lower()
            customer = db.query(Customer).filter(Customer.workspace_id == workspace_id, func.lower(Customer.email) == clean_id, Customer.status != "deleted").first()
            if customer: return customer
        else:
            search_values = CRMCustomerOps._get_phone_search_values(clean_id)
            customer = db.query(Customer).filter(Customer.workspace_id == workspace_id, Customer.phone.in_(search_values), Customer.status != "deleted").first()
            if customer: return customer

        # 3. Create New Guest if no match
        return CRMCustomerOps._create_guest(db, workspace_id, email=clean_id if is_email else None, phone=clean_id if not is_email else None, channel=channel, name=name)

    @staticmethod
    def create_customer(db: Session, workspace_id: str, data: dict):
        email = data.get("email", "").strip().lower()
        if email:
            existing = db.query(Customer).filter(Customer.workspace_id == workspace_id, func.lower(Customer.email) == email, Customer.status.notin_(['converted', 'deleted'])).first()
            if existing:
                CRMCustomerOps._update_customer_fields(existing, data)
                db.commit()
                return existing

        customer = Customer(
            id=generate_customer_id(), workspace_id=workspace_id,
            first_name=data.get("first_name"), last_name=data.get("last_name"),
            email=email, phone=data.get("phone"), status=data.get("status", "active"),
            plan=data.get("plan", "Starter"), customer_type=data.get("customer_type")
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def convert_to_customer(db: Session, customer_id: str, trigger: str):
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer: raise ValueError("Customer not found")
        if customer.customer_type == "customer": return customer

        customer.cust_id = customer.cust_id or generate_customer_id()
        customer.customer_type = "customer"
        customer.lifecycle_stage = "Customer"
        customer.converted_at = datetime.now(timezone.utc)
        customer.converted_by = trigger
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def _create_guest(db, workspace_id, email=None, phone=None, session_id=None, channel="chat", name=None):
        first_name, last_name = (name.split(" ", 1) + [None])[:2] if name else (None, None)
        guest = Customer(
            id=generate_guest_id(), workspace_id=workspace_id, session_id=session_id,
            email=email, phone=phone, first_name=first_name, last_name=last_name,
            customer_type="guest", status="active", lifecycle_stage="Subscriber"
        )
        db.add(guest)
        db.commit()
        return guest

    @staticmethod
    def _get_phone_search_values(phone):
        digits = "".join(filter(str.isdigit, phone))
        vals = {phone}
        if digits:
            vals.update([digits, f"+{digits}"])
            if len(digits) == 10: vals.add(f"1{digits}")
            if len(digits) == 11 and digits.startswith("1"): vals.add(digits[1:])
        return vals

    @staticmethod
    def _update_customer_fields(customer, data):
        for field in ["first_name", "last_name", "phone", "plan", "lifecycle_stage", "crm_status"]:
            if data.get(field): setattr(customer, field, data[field])
