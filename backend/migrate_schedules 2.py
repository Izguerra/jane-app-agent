
import os
import sys
from sqlalchemy import create_engine

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
         return "postgresql://postgres:postgres@localhost:54322/postgres"
    return url

def migrate():
    """Create worker_schedules table if not exists"""
    url = get_database_url()
    if not url:
        print("Error: DATABASE_URL not set")
        return

    print(f"Connecting to {url.split('@')[1] if '@' in url else url}...")
    engine = create_engine(url)
    
    # Import Base and the new model explicitly to ensure it's registered
    from backend.models_db import Base, WorkerSchedule
    
    print("Creating tables...")
    # This will strictly add tables that are defined in Base but missing in DB.
    # It will NOT modifying existing tables.
    Base.metadata.create_all(engine)
    print("Migration successful: Checked/Created worker_schedules table.")

if __name__ == "__main__":
    migrate()
