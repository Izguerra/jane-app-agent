from sqlalchemy import create_engine, text
import os
import sys

# Add parent directory to path to import backend modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.database import DATABASE_URL

def migrate_crm_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Migrating CRM schema...")
        
        # Check if 'customers' table exists
        # If it exists, we need to add new columns if they are missing
        # For simplicity in this dev environment, we'll try to add columns and ignore errors if they exist
        
        columns_to_add = [
            ("status", "VARCHAR(20) DEFAULT 'active' NOT NULL"),
            ("plan", "VARCHAR(50) DEFAULT 'Starter'"),
            ("usage_limit", "INTEGER DEFAULT 1000"),
            ("usage_used", "INTEGER DEFAULT 0"),
            ("avatar_url", "VARCHAR(255)"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()") 
        ]
        
        for col_name, col_def in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Skipping {col_name} (might exist): {e}")
                
        # Also ensure created_at is present in customers if not already
        
        conn.commit()
        print("CRM Schema Migration complete.")

if __name__ == "__main__":
    migrate_crm_schema()
