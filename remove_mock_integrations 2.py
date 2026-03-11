#!/usr/bin/env python3
"""Remove mock platform integrations from database"""

import sys
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

from backend.database import engine
from sqlalchemy import text

def remove_mock_integrations():
    """Remove all platform integrations"""
    print("🗑️  Removing mock platform integrations...")
    
    try:
        with engine.connect() as conn:
            # Delete all platform integrations
            result = conn.execute(text("DELETE FROM platform_integrations"))
            conn.commit()
            print(f"✅ Removed {result.rowcount} platform integrations")
            
            # Verify deletion
            result = conn.execute(text("SELECT COUNT(*) FROM platform_integrations"))
            count = result.scalar()
            print(f"📊 Remaining integrations: {count}")
            
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = remove_mock_integrations()
    sys.exit(0 if success else 1)
