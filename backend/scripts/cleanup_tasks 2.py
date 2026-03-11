
from backend.database import SessionLocal
from backend.services.worker_service import WorkerService

def cleanup_stuck_tasks():
    print("🧹 Cleaning up stuck tasks...")
    db = SessionLocal()
    try:
        service = WorkerService(db)
        # Get all running tasks
        tasks = service.get_workspace_tasks("wrk_000V7dMzXJLzP5mYgdf7FzjA3J", status="running", limit=100)
        
        count = 0
        for task in tasks:
            print(f"  - Marking task {task.id} ({task.worker_type}) as failed (Stale)")
            service.fail_task(task.id, "System cleanup: Task stopped due to staleness or restart.")
            count += 1
            
        print(f"✅ Cleaned up {count} stuck tasks.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_stuck_tasks()
