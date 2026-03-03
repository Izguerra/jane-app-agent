import sys
import os
import logging
from sqlalchemy import text

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_indexes")

def main():
    db = SessionLocal()
    try:
        # Dictionary of Table -> [Columns to Index]
        # We focus on foreign keys that are often queried but might not be indexed automatically
        indexes_to_add = {
            "communications": ["customer_id", "agent_id", "integration_id"], 
            "appointments": ["customer_id"],
            "deals": ["customer_id"],
            "campaign_enrollments": ["customer_id", "campaign_id"],
            "campaign_steps": ["campaign_id"],
            "phone_numbers": ["agent_id"],
            "integrations": ["agent_id"],
            "agents": ["workspace_id"],
            "customers": ["workspace_id"],
            "workspaces": ["team_id"],
            "team_members": ["user_id", "team_id"],
            "activity_logs": ["team_id", "user_id"]
        }
        
        with engine.connect() as conn:
            for table, columns in indexes_to_add.items():
                for column in columns:
                    index_name = f"ix_{table}_{column}"
                    
                    # Check if index exists (Postgres specific)
                    check_query = text(f"""
                        SELECT 1
                        FROM pg_indexes
                        WHERE tablename = :table
                        AND indexname = :index_name
                    """)
                    
                    result = conn.execute(check_query, {"table": table, "index_name": index_name}).fetchone()
                    
                    if not result:
                        logger.info(f"Creating index {index_name} on {table}({column})...")
                        try:
                            # CREATE INDEX CONCURRENTLY cannot run in a transaction block usually, 
                            # but with sqlalchemy execute it might be fine or we need to commit first.
                            # For simplicity/safety in this script, we'll try standard creation.
                             conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"))
                             conn.commit()
                             logger.info(f"Index {index_name} created.")
                        except Exception as e:
                            logger.error(f"Failed to create index {index_name}: {e}")
                            conn.rollback()
                    else:
                        logger.info(f"Index {index_name} already exists.")
                        
    except Exception as e:
        logger.error(f"Error during index creation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
