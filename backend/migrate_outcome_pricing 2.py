#!/usr/bin/env python3
"""
Migration script to add outcome-pricing columns to worker tables.
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
    # Worker Templates
    """
    ALTER TABLE worker_templates 
    ADD COLUMN IF NOT EXISTS outcome_price INTEGER DEFAULT 0;
    """,
    """
    ALTER TABLE worker_templates 
    ADD COLUMN IF NOT EXISTS evaluation_logic JSONB DEFAULT '{}'::jsonb;
    """,
    # Worker Tasks
    """
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS outcome_status VARCHAR(50) DEFAULT 'pending_eval';
    """,
    """
    ALTER TABLE worker_tasks 
    ADD COLUMN IF NOT EXISTS outcome_score FLOAT;
    """
]

print("Running outcome pricing migration...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

try:
    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            print(f"Running migration {i}/{len(migrations)}...")
            conn.execute(text(migration))
            conn.commit()
    
    print("✅ Migration completed successfully!")
    print("Added columns to worker_templates: outcome_price, evaluation_logic")
    print("Added columns to worker_tasks: outcome_status, outcome_score")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
