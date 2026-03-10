from backend.database import SessionLocal
from backend.models_db import Customer
from datetime import datetime, timedelta
import random

def populate_data():
    db = SessionLocal()
    try:
        print("Populating Last Active dates and Company names...")
        customers = db.query(Customer).all()
        
        count = 0
        now = datetime.now()
        
        company_suffixes = ["Inc", "LLC", "Corp", "Solutions", "Studios", "Global"]
        
        for c in customers:
            updated = False
            
            # Populate last_contact_date if missing
            if not c.last_contact_date:
                # Random time in last 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                c.last_contact_date = now - timedelta(days=days_ago, hours=hours_ago)
                updated = True
                
            # Populate company_name if missing
            if not c.company_name:
                suffix = random.choice(company_suffixes)
                c.company_name = f"{c.last_name} {suffix}"
                updated = True
                
            if updated:
                count += 1
                
        db.commit()
        print(f"✅ Updated {count} customers with data.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_data()
