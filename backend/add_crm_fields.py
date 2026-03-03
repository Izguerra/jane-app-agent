from backend.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as connection:
        # Check if columns exist to avoid errors
        # This is a basic migration script assuming PostgreSQL or SQLite
        
        # Lifecycle Stage
        try:
            connection.execute(text("ALTER TABLE customers ADD COLUMN lifecycle_stage VARCHAR(50)"))
            print("Added lifecycle_stage column")
        except Exception as e:
            print(f"Skipping lifecycle_stage (might exist): {e}")

        # CRM Status (Interaction Status)
        try:
            connection.execute(text("ALTER TABLE customers ADD COLUMN crm_status VARCHAR(50)"))
            print("Added crm_status column")
        except Exception as e:
            print(f"Skipping crm_status (might exist): {e}")
            
        # Customer Type
        try:
            connection.execute(text("ALTER TABLE customers ADD COLUMN customer_type VARCHAR(50)"))
            print("Added customer_type column")
        except Exception as e:
            print(f"Skipping customer_type (might exist): {e}")
            
        connection.commit()
        print("Migration complete")

if __name__ == "__main__":
    migrate()
