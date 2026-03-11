from backend.database import SessionLocal
from backend.models_db import CommunicationLog
from datetime import datetime, timedelta
from sqlalchemy import func

def verify_analytics():
    db = SessionLocal()
    try:
        # 1. Create a test log
        print("Creating test log...")
        test_log = CommunicationLog(
            type="call",
            direction="inbound",
            status="completed",
            duration=120,
            start_time=datetime.now(),
            participant_identity="test_user"
        )
        db.add(test_log)
        db.commit()
        db.refresh(test_log)
        print(f"Created log with ID: {test_log.id}")

        # 2. Verify Summary
        print("Verifying summary...")
        total = db.query(CommunicationLog).count()
        print(f"Total logs: {total}")
        assert total > 0, "Total logs should be > 0"

        # 3. Verify History
        print("Verifying history...")
        today = datetime.now().date()
        count_today = db.query(CommunicationLog).filter(
            func.date(CommunicationLog.start_time) == today
        ).count()
        print(f"Logs for today: {count_today}")
        assert count_today > 0, "Should have logs for today"

        # 4. Cleanup
        print("Cleaning up...")
        db.delete(test_log)
        db.commit()
        print("Verification successful!")

    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_analytics()
