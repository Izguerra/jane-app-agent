import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

if "sslmode=require" not in DATABASE_URL and "?" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")

engine = create_engine(DATABASE_URL)

def add_column():
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        print("Checking for confirmation_code column...")
        
        # Check if column exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='appointments' AND column_name='confirmation_code';
        """)
        result = conn.execute(check_query)
        if result.fetchone():
            print("Column 'confirmation_code' already exists.")
            return

        print("Adding confirmation_code column...")
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN confirmation_code VARCHAR(20)"))
            conn.execute(text("CREATE UNIQUE INDEX ix_appointments_confirmation_code ON appointments (confirmation_code)"))
            print("Successfully added confirmation_code column and index.")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
