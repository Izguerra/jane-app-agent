from sqlalchemy import create_engine, text
import os
import sys

# Add parent directory to path to import backend modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.database import DATABASE_URL

def add_indexes():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking/Adding indexes for analytics optimization...")
        
        # 1. Index on workspace_id (usually created by ForeignKey, but good to ensure for filtering)
        # Note: ForeignKey usually creates an index, but let's be explicit if needed or rely on the FK one.
        # Actually, standard FKs in Postgres often don't auto-create indices on the child table column.
        # Let's create a composite index for the most common query: WHERE workspace_id = X ORDER BY started_at DESC
        
        try:
            # Check if index exists
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_communications_workspace_started_at ON communications (workspace_id, started_at DESC)"))
            print("Successfully created index: idx_communications_workspace_started_at")
        except Exception as e:
            print(f"Error creating index: {e}")

        # 2. Index on started_at alone (for global time-based queries or if workspace filter is omitted)
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_communications_started_at ON communications (started_at DESC)"))
            print("Successfully created index: idx_communications_started_at")
        except Exception as e:
            print(f"Error creating index idx_communications_started_at: {e}")
            
        conn.commit()
        print("Index creation complete.")

if __name__ == "__main__":
    add_indexes()
