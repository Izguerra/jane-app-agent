
from backend.database import SessionLocal
from backend.models_db import WorkerTask
from sqlalchemy import desc

def verify_logs():
    print("--- VERIFYING WORKER TASK LOGS ---")
    db = SessionLocal()
    try:
        # Fetch last 20 tasks
        tasks = db.query(WorkerTask).order_by(desc(WorkerTask.created_at)).limit(20).all()
        
        print(f"Found {len(tasks)} recent tasks in Database:")
        print(f"{'ID':<36} | {'Worker Type':<20} | {'Status':<10} | {'Created At'}")
        print("-" * 100)
        
        for t in tasks:
            print(f"{str(t.id):<36} | {t.worker_type:<20} | {t.status:<10} | {t.created_at}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_logs()
