#!/usr/bin/env python3
"""
Test Twilio Outbound Calling

This script tests the new Twilio Programmable Voice outbound calling service.
"""

import os
import sys
import asyncio
import argparse

# Add project root to path
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

from dotenv import load_dotenv
load_dotenv()

from backend.services.outbound_calling_service import outbound_calling_service
from backend.database import SessionLocal
from backend.models_db import Workspace

async def test_twilio_outbound(to_phone):
    """Test Twilio outbound calling"""
    
    print('=' * 70)
    print('🧪 TESTING TWILIO OUTBOUND CALLING')
    print('=' * 70)
    print()
    
    # Check configuration
    print('Checking DB configuration for workspace...')
    print()
    
    # Get workspace
    db = SessionLocal()
    workspace = db.query(Workspace).first()
    
    if not workspace:
        print('❌ ERROR: No workspace found')
        db.close()
        return
    
    print(f'✅ Workspace: {workspace.id}')
    print()
    
    # Initiate call
    print('Initiating outbound call...')
    print(f'  To: {to_phone}')
    print(f'  Purpose: Test call')
    print()
    
    try:
        result = await outbound_calling_service.initiate_call(
            workspace_id=workspace.id,
            to_phone=to_phone,
            call_intent='test_outbound',
            call_context={
                'test': 'Telnyx outbound calling',
                'timestamp': str(asyncio.get_event_loop().time())
            },
            provider="telnyx",
            from_phone="+18382061295",
            db=db
        )
        
        print('=' * 70)
        print('✅ CALL INITIATED SUCCESSFULLY!')
        print('=' * 70)
        print()
        print(f'Communication ID: {result.get("communication_id")}')
        print(f'Telephony Provider ID: {result.get("twilio_call_sid") or result.get("telnyx_call_id") or "N/A"}')
        print(f'Status: {result["status"]}')
        print()
        print('🔔 YOUR PHONE SHOULD BE RINGING!')
        print('   1. Answer the call')
        print('   2. You should connect to the LiveKit agent')
        print()
        print('=' * 70)
        
    except Exception as e:
        print('=' * 70)
        print('❌ ERROR')
        print('=' * 70)
        print()
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        print()
    
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Twilio Outbound Call')
    parser.add_argument('--phone', type=str, default='+14167865786', help='Phone number to dial (E.164)')
    args = parser.parse_args()
    
    asyncio.run(test_twilio_outbound(args.phone))
