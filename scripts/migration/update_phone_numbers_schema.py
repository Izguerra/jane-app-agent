from sqlalchemy import text
from backend.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    db = SessionLocal()
    try:
        # Check if columns exist
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='phone_numbers';"))
        columns = [row[0] for row in result.fetchall()]
        
        if 'agent_id' not in columns:
            logger.info("Adding agent_id column to phone_numbers...")
            db.execute(text("ALTER TABLE phone_numbers ADD COLUMN agent_id VARCHAR(20) REFERENCES agents(id);"))
        else:
            logger.info("agent_id column already exists.")

        if 'stripe_subscription_item_id' not in columns:
            logger.info("Adding stripe_subscription_item_id column to phone_numbers...")
            db.execute(text("ALTER TABLE phone_numbers ADD COLUMN stripe_subscription_item_id VARCHAR(255);"))
        else:
            logger.info("stripe_subscription_item_id column already exists.")

        db.commit()
        logger.info("Schema update complete.")
        
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_schema()
