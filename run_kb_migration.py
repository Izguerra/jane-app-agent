#!/usr/bin/env python3
"""Run knowledge base sources migration"""

import sys
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

from backend.database import engine
from sqlalchemy import text
from pathlib import Path

def run_migration():
    """Execute the knowledge base sources migration"""
    migration_file = Path(__file__).parent / "migrations" / "004_create_knowledge_base_sources.sql"
    
    print(f"📄 Reading migration file: {migration_file}")
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    print("🔄 Executing migration...")
    try:
        with engine.connect() as conn:
            conn.execute(text(sql_content))
            conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify table was created
        print("\n🔍 Verifying table...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'knowledge_base_sources'
            """))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✅ Table created: {tables[0]}")
            else:
                print("⚠️  Table not found")
                return False
            
            # Check columns added to documents table
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' 
                AND column_name IN ('source_id', 'sync_status', 'metadata')
                ORDER BY column_name
            """))
            columns = [row[0] for row in result]
            print(f"✅ Columns added to documents: {', '.join(columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
