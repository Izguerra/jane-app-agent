from backend.database import SessionLocal
from backend.models_db import Customer, User
from sqlalchemy import desc

def check_sort():
    db = SessionLocal()
    try:
        print("Checking Customer Sort Order (Newest First)...")
        customers = db.query(Customer).order_by(desc(Customer.created_at)).limit(10).all()
        
        for c in customers:
            print(f"Customer: {c.first_name} {c.last_name}")
            print(f"  - Email: {c.email}")
            print(f"  - Created At: {c.created_at}")
            print(f"  - Workspace: {c.workspace_id}")
            
            # Check for matching user
            user = db.query(User).filter(User.email == c.email).first()
            if user:
                print(f"  - [WARNING] MATCHING USER FOUND: Role={user.role}")
            else:
                print(f"  - No matching user found (Safe)")
                
            print("-" * 30)
            
    finally:
        db.close()

if __name__ == "__main__":
    check_sort()
