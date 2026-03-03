import os
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_worker_instances():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id, name, worker_type, status, container_id FROM worker_instances WHERE worker_type = 'openclaw';"))
        rows = result.fetchall()
        print(f"Found {len(rows)} OpenClaw instances:")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_worker_instances()
