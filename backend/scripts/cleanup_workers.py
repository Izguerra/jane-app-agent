import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
     DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def cleanup_instances():
    with engine.connect() as conn:
        print("Cleaning up ghost worker instances...")
        conn.execute(text("UPDATE worker_instances SET status = 'terminated' WHERE status != 'terminated'"))
        conn.commit()
        print("Done.")

if __name__ == "__main__":
    cleanup_instances()
