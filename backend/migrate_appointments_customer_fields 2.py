#!/usr/bin/env python3
"""
Migration script to add customer contact fields to appointments table.
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

migrations = [
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS customer_first_name VARCHAR(100);",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS customer_last_name VARCHAR(100);",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(50);",
    "ALTER TABLE appointments ALTER COLUMN customer_id DROP NOT NULL;",  # Make customer_id nullable
]

print("Adding customer contact fields to appointments table...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

try:
    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            print(f"Running migration {i}/{len(migrations)}...")
            conn.execute(text(migration))
            conn.commit()
        
        print("✅ Added all customer contact fields to appointments table")
    
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
