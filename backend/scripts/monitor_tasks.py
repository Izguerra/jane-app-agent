import time
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
     DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def monitor():
    print("Monitoring tasks...")
    seen_status = {}
    with engine.connect() as conn:
        while True:
            result = conn.execute(text("SELECT id, status, worker_type FROM worker_tasks ORDER BY created_at DESC LIMIT 1")).fetchone()
            if result:
                task_id, status, wtype = result
                key = f"{task_id}_{status}"
                if key not in seen_status:
                    print(f"Task {task_id} ({wtype}): {status}", flush=True)
                    seen_status[key] = True
            time.sleep(1)

if __name__ == "__main__":
    monitor()
