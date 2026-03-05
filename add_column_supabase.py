
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    print("POSTGRES_URL not found in .env")
    exit(1)

# Fix postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def add_column():
    print(f"Connecting to {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'DB'}...")
    with engine.connect() as conn:
        print("Adding 'allowed_worker_types' column to 'agents' table...")
        try:
            conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS allowed_worker_types JSON DEFAULT '[]';"))
            conn.commit()
            print("Successfully added column!")
        except Exception as e:
            print(f"Error adding column: {e}")
            
        print("Checking if 'agent_skills' and 'agent_personalities' tables exist...")
        # Since create_all didn't seem to work, let's try manual checks
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")).fetchall()
        table_names = [t[0] for t in tables]
        print(f"Current tables: {table_names}")

if __name__ == "__main__":
    add_column()
