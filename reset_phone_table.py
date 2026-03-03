from backend.database import engine, Base
from backend.models_db import PhoneNumber
from sqlalchemy import text

def reset_table():
    print("Dropping phone_numbers table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS phone_numbers CASCADE"))
        conn.commit()
    
    print("Recreating phone_numbers table...")
    # Create only the PhoneNumber table
    PhoneNumber.__table__.create(bind=engine)
    print("Table 'phone_numbers' recreated with new schema.")

if __name__ == "__main__":
    reset_table()
