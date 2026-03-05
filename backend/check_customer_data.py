from backend.database import SessionLocal
from backend.models_db import Customer
from sqlalchemy import desc

def check_data():
    db = SessionLocal()
    try:
        print("Checking Customer Data for new columns...")
        customers = db.query(Customer).limit(10).all()
        
        for c in customers:
            print(f"Customer: {c.first_name} {c.last_name}")
            print(f"  - Company: {c.company_name}")
            print(f"  - Last Contact: {c.last_contact_date}")
            print(f"  - Updated At: {c.updated_at}")
            print("-" * 30)
            
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
