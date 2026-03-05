import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import engine
from sqlalchemy import text

def migrate():
    print("Running migration: 006_add_retention_policy")
    
    with engine.connect() as conn:
        # Check if column exists first to avoid errors
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='workspaces' AND column_name='retention_days'"))
        if result.fetchone():
            print("Column 'retention_days' already exists. Skipping.")
        else:
            print("Adding 'retention_days' column...")
            conn.execute(text("ALTER TABLE workspaces ADD COLUMN retention_days INTEGER DEFAULT 30"))
            
        # Check for data_collection_opt_out
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='workspaces' AND column_name='data_collection_opt_out'"))
        if result.fetchone():
            print("Column 'data_collection_opt_out' already exists. Skipping.")
        else:
            print("Adding 'data_collection_opt_out' column...")
            conn.execute(text("ALTER TABLE workspaces ADD COLUMN data_collection_opt_out BOOLEAN DEFAULT FALSE"))
            
        # Commit transaction
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
