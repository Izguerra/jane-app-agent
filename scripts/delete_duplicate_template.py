import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def delete_duplicate():
    # ID for "Clawdbot Browser Agent"
    duplicate_id = "10e274a6-5cd1-44d0-80ea-f9bb63ec3388"
    
    with engine.connect() as conn:
        print(f"Deleting template with ID: {duplicate_id}")
        result = conn.execute(text("DELETE FROM worker_templates WHERE id = :id"), {"id": duplicate_id})
        conn.commit()
        print(f"Deleted {result.rowcount} row(s).")

if __name__ == "__main__":
    delete_duplicate()
