import sys
import os
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models_db import Workspace, Communication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_data")

def main():
    db = SessionLocal()
    try:
        # Get all workspaces with retention enabled (retention_days > 0)
        # We process workspace by workspace to respect individual settings
        workspaces = db.query(Workspace).filter(Workspace.retention_days > 0).all()
        
        logger.info(f"Found {len(workspaces)} workspaces with retention policies.")
        
        total_deleted = 0
        
        for workspace in workspaces:
            days = workspace.retention_days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            logger.info(f"Workspace {workspace.name} ({workspace.id}): keeping {days} days, cleaning before {cutoff_date.date()}")
            
            # Delete communications older than cutoff
            # Note: Cascade delete should handle related messages if configured, 
            # otherwise we might need to delete from conversation_messages first.
            # Assuming Communication is the parent of messages/recordings.
            
            # Count first
            count_q = db.query(Communication).filter(
                Communication.workspace_id == workspace.id,
                Communication.started_at < cutoff_date
            )
            count = count_q.count()
            
            if count > 0:
                logger.info(f"  Deleting {count} old communications...")
                # Bulk delete using ORM is slow, raw SQL is faster but bypasses some session logic.
                # ORM delete:
                count_q.delete(synchronize_session=False)
                total_deleted += count
            else:
                logger.info("  No data to clean.")
                
        if total_deleted > 0:
            db.commit()
            logger.info(f"Total cleanup complete. Deleted {total_deleted} records.")
        else:
            logger.info("Cleanup complete. No records deleted.")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
