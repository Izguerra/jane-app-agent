from backend.database import SessionLocal
from backend.services.crm_service import CRMService
from backend.models_db import Communication

class CustomerTools:
    def __init__(self, workspace_id: int, communication_id: str = None):
        self.workspace_id = workspace_id
        self.communication_id = communication_id

    def register_customer(self, first_name: str, last_name: str, phone: str = None, email: str = None) -> str:
        """
        Register a user as a Customer in the system and link them to the current conversation.
        Use this tool IMMEDIATELY after obtaining the user's First and Last Name.
        
        :param first_name: The user's first name
        :param last_name: The user's last name
        :param phone: Optional phone number if provided
        :param email: Optional email if provided
        :return: Success message
        """
        db = SessionLocal()
        try:
            crm_service = CRMService(db)
            
            # Use the centralized create_customer logic (Strict Email Priority + Upsert)
            customer_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "status": "active"
            }
            
            customer = crm_service.create_customer(self.workspace_id, customer_data)
            
            # 2. Link to Communication (Context)
            if self.communication_id:
                comm = db.query(Communication).filter(Communication.id == self.communication_id).first()
                if comm:
                    comm.customer_id = customer.id
                    # Snapshot fields for logs
                    comm.customer_first_name = customer.first_name
                    comm.customer_last_name = customer.last_name
                    comm.customer_email = customer.email
                    comm.customer_phone = customer.phone
                    db.commit()
            
            return f"Successfully registered/updated profile for {customer.first_name} {customer.last_name}."
            
        except Exception as e:
            return f"Error registering customer: {str(e)}"
        finally:
            db.close()

    def check_registration_status(self, email: str = None, phone: str = None) -> str:
        """
        Check if a customer is already registered by their email or phone number.
        Use this tool to find existing profiles BEFORE asking for Name or Registering.
        
        :param email: The user's email address
        :param phone: The user's phone number
        :return: Status message with Name if found, or 'Not Found'.
        """
        if not email and not phone:
             return "Please provide an email or phone number to check."

        db = SessionLocal()
        try:
            from backend.models_db import Customer
            from sqlalchemy import func
            
            customer = None
            if email:
                customer = db.query(Customer).filter(
                    Customer.workspace_id == self.workspace_id,
                    func.lower(Customer.email) == email.lower(),
                    Customer.status.notin_(['converted', 'deleted'])
                ).first()
                
            if not customer and phone:
                 # Robust phone check: generate common formats to match against DB
                 clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
                 
                 # Store variations to check
                 phone_variations = [
                     clean_phone,
                     f"+{clean_phone}",
                     f"1{clean_phone}", 
                     f"+1{clean_phone}",
                 ]
                 
                 # Add formatted variations if length is 10
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
                    Customer.phone.in_(phone_variations),
                    Customer.status.notin_(['converted', 'deleted'])
                 ).first()
            
            if customer:
                # Link to current comm if found? Optional, but good practice for context.
                if self.communication_id:
                     comm = db.query(Communication).filter(Communication.id == self.communication_id).first()
                     if comm and not comm.customer_id:
                         print(f"DEBUG: Linking Found Customer {customer.id} to Comm {comm.id}")
                         comm.customer_id = customer.id
                         db.commit()
                
                return f"FOUND: Customer profile found for {customer.first_name} {customer.last_name}. You may proceed with verification."
            else:
                return "NOT FOUND: No existing customer profile found with those details."
                
        except Exception as e:
            return f"Error checking registration: {str(e)}"
        finally:
            db.close()
