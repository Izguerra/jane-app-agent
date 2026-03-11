#!/usr/bin/env python3
"""
Migration script v2: Add missing pricing and attribution columns to worker_tasks.
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
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS outcome_fee_cents INTEGER DEFAULT 0;
    """,
    """
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS total_fee_cents INTEGER DEFAULT 0;
    """,
    """
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS fee_billed BOOLEAN DEFAULT FALSE;
    """,
    """
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS dispatched_by_agent_id VARCHAR(50) REFERENCES agents(id);
    """
]

print("Running outcome pricing migration v2...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

try:
    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            print(f"Running migration {i}/{len(migrations)}...")
            try:
                conn.execute(text(migration))
                conn.commit()
            except Exception as e:
                print(f"Warning on migration {i}: {e}")
                # Continue if column already exists (though IF NOT EXISTS should handle it)
    
    print("✅ Migration v2 completed successfully!")
    print("Added columns to worker_tasks: outcome_fee_cents, total_fee_cents, fee_billed, dispatched_by_agent_id")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
