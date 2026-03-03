#!/usr/bin/env python3
"""
Migration script to add outbound calling columns to communications table.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL or POSTGRES_URL must be set")
    sys.exit(1)

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# SQL statements to add missing columns
migrations = [
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS call_intent TEXT;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS call_outcome TEXT;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS call_context JSONB;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS customer_id VARCHAR(20);
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS twilio_call_sid TEXT;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS parent_communication_id VARCHAR(20);
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS campaign_id TEXT;
    """,
    """
    ALTER TABLE communications 
    ADD COLUMN IF NOT EXISTS campaign_name TEXT;
    """
]

print("Running communications table migration...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

try:
    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            print(f"Running migration {i}/{len(migrations)}...")
            conn.execute(text(migration))
            conn.commit()
    
    print("✅ Migration completed successfully!")
    print("Added columns: call_intent, call_outcome, call_context, customer_id, twilio_call_sid, retry_count, parent_communication_id, campaign_id, campaign_name")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
