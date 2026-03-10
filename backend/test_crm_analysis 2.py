import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if running on a different port
# Using the first customer found in the DB (would be better to fetch one dynamically or hardcode a known ID)
# For this test script, we'll try to fetch the list first to get an ID.

def test_crm_analysis():
    print("Fetching a customer to test with...")
    # NOTE: This requires authentication in a real scenario. 
    # Since we are running outside the authenticated web context, we might need a workaround 
    # OR we can just use the service directly in a python script if we import the modules.
    
    # However, testing the endpoint ensures the full flow works including API keys from env.
    # But dealing with AuthUser dependency in the router via script is hard without a valid token.
    
    # ALTERNATIVE: Direct Service Test
    # This avoids auth complications for this quick verification.
    from backend.database import SessionLocal
    from backend.services.crm_service import CRMService
    from backend.models_db import Customer
    
    db = SessionLocal()
    try:
        customer = db.query(Customer).first()
        if not customer:
            print("No customers found in DB to test.")
            return

        print(f"Testing with Customer: {customer.first_name} (ID: {customer.id})")
        print(f"Current State: Stage={customer.lifecycle_stage}, Status={customer.crm_status}, Type={customer.customer_type}")
        
        # Test Case 1: Upgrade to SQL (Asking for demo)
        interaction_text = "I'm really interested in the enterprise plan. Can we book a demo for next Tuesday?"
        print(f"\nSimulating Interaction: '{interaction_text}'")
        
        service = CRMService(db)
        result = service.analyze_and_update_customer_status(customer.id, interaction_text)
        
        print("Analysis Result:", json.dumps(result, indent=2))
        
        # Reload to verify DB
        db.refresh(customer)
        print(f"New State: Stage={customer.lifecycle_stage}, Status={customer.crm_status}, Type={customer.customer_type}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_crm_analysis()
