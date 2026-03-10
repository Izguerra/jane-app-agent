"""
Simplified script to add dummy customer data only
"""
from backend.database import SessionLocal
from backend.models_db import Customer, Workspace
from datetime import datetime, timedelta
import secrets
import string

def generate_id(prefix='cus_', length=12):
    """Generate a random ID with prefix"""
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_part}"

def seed_customers():
    db = SessionLocal()
    
    try:
        # Get the first workspace
        workspace = db.query(Workspace).first()
        if not workspace:
            print("No workspace found. Please run the main seed script first.")
            return
        
        print(f"Using workspace: {workspace.id}")
        
        # Sample customer data
        customers_data = [
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@techcorp.com",
                "phone": "+1-555-0101",
                "company_name": "TechCorp Solutions",
                "plan": "Professional",
                "status": "active",
                "usage_used": 45,
                "usage_limit": 100
            },
            {
                "first_name": "Michael",
                "last_name": "Chen",
                "email": "m.chen@innovate.io",
                "phone": "+1-555-0102",
                "company_name": "Innovate Inc",
                "plan": "Enterprise",
                "status": "active",
                "usage_used": 87,
                "usage_limit": 200
            },
            {
                "first_name": "Emma",
                "last_name": "Davis",
                "email": "emma.d@startuplab.com",
                "phone": "+1-555-0103",
                "company_name": "Startup Lab",
                "plan": "Starter",
                "status": "active",
                "usage_used": 12,
                "usage_limit": 50
            },
            {
                "first_name": "James",
                "last_name": "Wilson",
                "email": "jwilson@enterprise.com",
                "phone": "+1-555-0104",
                "company_name": "Enterprise Global",
                "plan": "Enterprise",
                "status": "active",
                "usage_used": 156,
                "usage_limit": 200
            },
            {
                "first_name": "Sofia",
                "last_name": "Martinez",
                "email": "sofia@creativestudio.com",
                "phone": "+1-555-0105",
                "company_name": "Creative Studio",
                "plan": "Professional",
                "status": "active",
                "usage_used": 67,
                "usage_limit": 100
            },
        ]
        
        # Create customers
        created_at_base = datetime.now() - timedelta(days=90)
        for i, data in enumerate(customers_data):
            customer = Customer(
                id=generate_id('cus_'),
                workspace_id=workspace.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                phone=data["phone"],
                company_name=data["company_name"],
                plan=data["plan"],
                status=data["status"],
                usage_used=data["usage_used"],
                usage_limit=data["usage_limit"],
                created_at=created_at_base + timedelta(days=i*15)
            )
            db.add(customer)
        
        db.commit()
        print(f"✅ Created {len(customers_data)} customers")
        print("\n🎉 Customer data seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_customers()
