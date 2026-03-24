from livekit.agents import llm
from backend.database import SessionLocal
from backend.services.crm_service import CRMService
from backend.models_db import Customer, Deal

class CRMMixin:
    @llm.function_tool(description="Check if a customer is already registered.")
    async def check_registration_status(self, email: str = None, phone: str = None):
        from backend.tools.customer_tools import CustomerTools
        tools = CustomerTools(workspace_id=self.workspace_id)
        return tools.check_registration_status(email, phone)

    @llm.function_tool(description="Search for customers in the CRM.")
    async def search_customers(self, query: str):
        db = SessionLocal()
        try:
            crm = CRMService(db)
            res = crm.get_customers(workspace_id=self.workspace_id, search=query)
            customers = res.get("items", [])
            return "\n".join([f"- {c.first_name} {c.last_name} ({c.email})" for c in customers]) or "No customers found."
        except Exception as e:
            return f"Error searching customers: {str(e)}"
        finally: db.close()

    @llm.function_tool(description="Update an existing customer record with new information.")
    async def update_customer_record(self, customer_id: str, first_name: str = None, last_name: str = None, email: str = None, phone: str = None, notes: str = None):
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id, Customer.workspace_id == self.workspace_id).first()
            if not customer: return "Customer not found."
            updates = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone, "notes": notes}
            for k, v in updates.items():
                if v is not None and hasattr(customer, k): setattr(customer, k, v)
            db.commit()
            return f"Updated customer {customer_id}."
        except Exception as e:
            return f"Error updating customer: {str(e)}"
        finally: db.close()

    @llm.function_tool(description="List active sales deals.")
    async def list_deals(self, stage: str = None):
        db = SessionLocal()
        try:
            query = db.query(Deal).filter(Deal.workspace_id == self.workspace_id)
            if stage: query = query.filter(Deal.stage == stage)
            deals = query.all()
            return "\n".join([f"- {d.title}: ${d.value/100:.2f}" for d in deals]) or "No deals found."
        except Exception as e:
            return f"Error listing deals: {str(e)}"
        finally: db.close()
