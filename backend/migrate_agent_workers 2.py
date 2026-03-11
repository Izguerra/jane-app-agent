import os
import sys
from sqlalchemy import create_engine, text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        url = os.getenv("POSTGRES_URL")
    if not url:
         # Fallback to local if env var missing (e.g. Supabase unrelated)
         return "postgresql://postgres:postgres@localhost:54322/postgres"
    return url

def migrate():
    """Add allowed_worker_types column to agents table"""
    url = get_database_url()
    if not url:
        print("Error: DATABASE_URL not set")
        return

    engine = create_engine(url)
    
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        
        # Check if column exists
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='agents' AND column_name='allowed_worker_types'"
        ))
        
        if result.rowcount == 0:
            print("Adding allowed_worker_types to agents table...")
            try:
                conn.execute(text("ALTER TABLE agents ADD COLUMN allowed_worker_types JSONB DEFAULT '[]'"))
                print("Migration successful: Added allowed_worker_types column.")
            except Exception as e:
                print(f"Error adding column: {e}")
        else:
            print("Column allowed_worker_types already exists.")

if __name__ == "__main__":
    migrate()
