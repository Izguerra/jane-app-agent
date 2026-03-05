#!/usr/bin/env python3
"""Test script to debug admin settings endpoints"""

import sys
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

from backend.database import SessionLocal
from sqlalchemy import text

# Test database connection and tables
db = SessionLocal()
try:
    # Test admin_settings table
    result = db.execute(text("SELECT * FROM admin_settings LIMIT 1")).fetchone()
    print("✓ admin_settings table exists")
    print(f"  Data: {result}")
    
    # Test platform_integrations table
    result = db.execute(text("SELECT * FROM platform_integrations LIMIT 3")).fetchall()
    print(f"\n✓ platform_integrations table exists ({len(result)} rows)")
    for row in result:
        print(f"  - {row[2]}: {row[1]}")
    
    # Test api_keys table
    result = db.execute(text("SELECT COUNT(*) FROM api_keys")).fetchone()
    print(f"\n✓ api_keys table exists ({result[0]} rows)")
    
    # Test active_sessions table
    result = db.execute(text("SELECT COUNT(*) FROM active_sessions")).fetchone()
    print(f"✓ active_sessions table exists ({result[0]} rows)")
    
    print("\n✅ All tables exist and are accessible!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
