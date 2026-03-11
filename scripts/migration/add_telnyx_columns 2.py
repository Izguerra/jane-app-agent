from sqlalchemy import text
from backend.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    db = SessionLocal()
    try:
        # Check phone_numbers table
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='phone_numbers';"))
        pn_columns = [row[0] for row in result.fetchall()]
        
        if 'provider' not in pn_columns:
            logger.info("Adding provider column to phone_numbers...")
            db.execute(text("ALTER TABLE phone_numbers ADD COLUMN provider VARCHAR(50) DEFAULT 'twilio' NOT NULL;"))
        
        if 'telnyx_id' not in pn_columns:
            logger.info("Adding telnyx_id column to phone_numbers...")
            db.execute(text("ALTER TABLE phone_numbers ADD COLUMN telnyx_id VARCHAR(255) UNIQUE;"))

        # Check communications table
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='communications';"))
        comm_columns = [row[0] for row in result.fetchall()]
        
        if 'telnyx_call_id' not in comm_columns:
            logger.info("Adding telnyx_call_id column to communications...")
            db.execute(text("ALTER TABLE communications ADD COLUMN telnyx_call_id TEXT;"))

        db.commit()
        logger.info("Database schema update for Telnyx complete.")
        
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_schema()
