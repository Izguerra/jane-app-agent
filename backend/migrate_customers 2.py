#!/usr/bin/env python3
"""
Migration script to fix customers table schema.
The customers table needs an 'id' column as primary key.
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

print("Checking customers table schema...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

try:
    with engine.connect() as conn:
        # Check if id column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customers' AND column_name = 'id'
        """))
        
        has_id = result.fetchone() is not None
        
        if has_id:
            print("✅ Customers table already has 'id' column")
        else:
            print("⚠️  Customers table is missing 'id' column")
            print("Adding 'id' column as primary key...")
            
            # Add id column with default values
            conn.execute(text("""
                ALTER TABLE customers 
                ADD COLUMN IF NOT EXISTS id VARCHAR(20) PRIMARY KEY DEFAULT 'cus_' || substr(md5(random()::text), 1, 16);
            """))
            conn.commit()
            
            print("✅ Added 'id' column to customers table")
    
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
