import logging
from livekit.agents import llm
from sqlalchemy.orm import Session

from backend.models_db import Customer
from backend.database import SessionLocal, generate_customer_id

logger = logging.getLogger("customer-tools")

class CustomerTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    @llm.function_tool(description="Check registration status.")
    def check_registration_status(self, email: str = None, phone: str = None) -> str:
        """
        Check registration status.
        Args:
            email: Email to check
            phone: Phone to check
        """
        db = SessionLocal()
        try:
            query = db.query(Customer).filter(Customer.workspace_id == self.workspace_id)
            if email:
                query = query.filter(Customer.email == email)
            elif phone:
                query = query.filter(Customer.phone == phone)
            else:
                return "Please provide an email or phone number."
            
            customer = query.first()
            if customer:
                return f"Customer found: {customer.first_name} {customer.last_name}"
            else:
                return "Customer not found."
        except Exception as e:
            logger.error(f"Error checking registration: {e}")
            return "Error checking registration status."
        finally:
            db.close()

    @llm.function_tool(description="Register a new customer.")
    def register_customer(self, first_name: str, last_name: str, phone: str = None, email: str = None) -> str:
        """
        Register a new customer.
        Args:
           first_name: First Name
           last_name: Last Name
           phone: Phone
           email: Email
        """
        db = SessionLocal()
        try:
            # Check existence
            query = db.query(Customer).filter(Customer.workspace_id == self.workspace_id)
            if email:
                exists = query.filter(Customer.email == email).first()
            elif phone:
                exists = query.filter(Customer.phone == phone).first()
            else:
                exists = None
                
            if exists:
                return f"Customer already registered: {exists.first_name} {exists.last_name}"
            
            new_customer = Customer(
                id=generate_customer_id(),
                workspace_id=self.workspace_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                status="active",
                customer_type="b2c"
            )
            db.add(new_customer)
            db.commit()
            return f"Successfully registered {first_name} {last_name}."
        except Exception as e:
            logger.error(f"Error registering customer: {e}")
            return "Failed to register customer."
        finally:
            db.close()
