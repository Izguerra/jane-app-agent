#!/usr/bin/env python3
"""Add real platform integrations to database"""

import sys
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

from backend.database import engine
from sqlalchemy import text

def add_real_integrations():
    """Add Stripe, WhatsApp, and Google Calendar integrations"""
    print("➕ Adding real platform integrations...")
    
    integrations = [
        {
            'provider': 'stripe',
            'display_name': 'Stripe',
            'description': 'Sync customer billing data and handle subscription payments automatically.',
            'is_enabled': True
        },
        {
            'provider': 'whatsapp',
            'display_name': 'WhatsApp',
            'description': 'Enable customer support conversations through WhatsApp Business API.',
            'is_enabled': True
        },
        {
            'provider': 'google_calendar',
            'display_name': 'Google Calendar',
            'description': 'Sync appointments and schedule meetings directly in Google Calendar.',
            'is_enabled': True
        }
    ]
    
    try:
        with engine.connect() as conn:
            for integration in integrations:
                conn.execute(text("""
                    INSERT INTO platform_integrations (provider, display_name, description, is_enabled)
                    VALUES (:provider, :display_name, :description, :is_enabled)
                    ON CONFLICT (provider) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        is_enabled = EXCLUDED.is_enabled
                """), integration)
                print(f"  ✅ Added {integration['display_name']}")
            
            conn.commit()
            
            # Verify
            result = conn.execute(text("SELECT COUNT(*) FROM platform_integrations"))
            count = result.scalar()
            print(f"\n📊 Total integrations: {count}")
            
            # List all
            result = conn.execute(text("SELECT provider, display_name FROM platform_integrations ORDER BY provider"))
            print("\n📋 Current integrations:")
            for row in result:
                print(f"  - {row[1]} ({row[0]})")
            
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_real_integrations()
    sys.exit(0 if success else 1)
