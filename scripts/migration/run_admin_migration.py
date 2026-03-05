#!/usr/bin/env python3
"""Run admin settings migration on PostgreSQL database"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import engine
from sqlalchemy import text

def run_migration():
    """Execute the admin settings migration"""
    migration_file = Path(__file__).parent / "migrations" / "003_create_admin_settings_tables.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Reading migration file: {migration_file}")
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    print("🔄 Executing migration...")
    try:
        with engine.connect() as conn:
            # Execute the entire SQL file
            conn.execute(text(sql_content))
            conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify tables were created
        print("\n🔍 Verifying tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('admin_settings', 'api_keys', 'active_sessions', 'platform_integrations')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if len(tables) == 4:
                print(f"✅ All 4 tables created: {', '.join(tables)}")
            else:
                print(f"⚠️  Only {len(tables)} tables found: {', '.join(tables)}")
        
        # Check data
        print("\n📊 Checking initial data...")
        with engine.connect() as conn:
            # Check admin_settings
            result = conn.execute(text("SELECT COUNT(*) FROM admin_settings"))
            count = result.scalar()
            print(f"  - admin_settings: {count} row(s)")
            
            # Check platform_integrations
            result = conn.execute(text("SELECT COUNT(*) FROM platform_integrations"))
            count = result.scalar()
            print(f"  - platform_integrations: {count} row(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
