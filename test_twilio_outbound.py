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

# Load environment variables
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

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
    print('Checking configuration...')
    if not os.getenv("TWILIO_ACCOUNT_SID"):
        print('❌ ERROR: TWILIO_ACCOUNT_SID not set')
        return
        
    print(f'✅ Twilio Account SID: {os.getenv("TWILIO_ACCOUNT_SID")[:6]}...')
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
                'test': 'Twilio outbound calling',
                'timestamp': str(asyncio.get_event_loop().time())
            },
            db=db
        )
        
        print('=' * 70)
        print('✅ CALL INITIATED SUCCESSFULLY!')
        print('=' * 70)
        print()
        print(f'Communication ID: {result["communication_id"]}')
        print(f'Twilio Call SID: {result["twilio_call_sid"]}')
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
