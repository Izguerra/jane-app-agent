from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import os
import logging

# Load env directly to be sure we get the same one as database.py
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("No database URL found!")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Check if table exists first
    if not inspector.has_table("communications"):
        logger.error("Table 'communications' does not exist! Run init_db first.")
        return

    columns = [c['name'] for c in inspector.get_columns('communications')]
    logger.info(f"Existing columns: {columns}")
    
    new_cols = {
        'summary': 'TEXT',
        'sentiment': 'VARCHAR(20)',
        'recording_url': 'TEXT',
        'channel': 'VARCHAR(50)', 
        'user_identifier': 'VARCHAR(255)'
    }
    
    with engine.connect() as conn:
        for col, dtype in new_cols.items():
            if col not in columns:
                logger.info(f"Adding column '{col}' to communications table...")
                conn.execute(text(f"ALTER TABLE communications ADD COLUMN {col} {dtype}"))
                conn.commit() # Explicit commit for DDL
            else:
                logger.info(f"Column '{col}' already exists.")

if __name__ == "__main__":
    print(f"Migrating DB...")
    migrate()
    print("Done.")
