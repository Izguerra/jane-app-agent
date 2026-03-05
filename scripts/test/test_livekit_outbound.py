#!/usr/bin/env python3
"""
Test LiveKit SIP Outbound Calling

This script tests the new LiveKit SIP outbound calling service.
"""

import os
import sys
import asyncio

sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

# Load environment variables
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from backend.services.livekit_outbound_service import livekit_outbound_service
from backend.database import SessionLocal
from backend.models_db import Workspace


async def test_livekit_outbound():
    """Test LiveKit SIP outbound calling"""
    
    print('=' * 70)
    print('🧪 TESTING LIVEKIT SIP OUTBOUND CALLING')
    print('=' * 70)
    print()
    
    # Check configuration
    print('Checking configuration...')
    sip_trunk_id = os.getenv('LIVEKIT_SIP_TRUNK_ID')
    if not sip_trunk_id:
        print('❌ ERROR: LIVEKIT_SIP_TRUNK_ID not set in .env')
        print()
        print('Please follow instructions in LIVEKIT_SIP_SETUP.md to:')
        print('1. Create a SIP trunk in LiveKit console')
        print('2. Add LIVEKIT_SIP_TRUNK_ID to .env')
        return
    
    print(f'✅ SIP Trunk ID: {sip_trunk_id}')
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
    print(f'  To: +14167865786 (Randy Esguerra)')
    print(f'  Purpose: Test call')
    print()
    
    try:
        result = await livekit_outbound_service.initiate_outbound_call(
            workspace_id=workspace.id,
            to_phone='+14167865786',
            call_intent='test',
            call_context={
                'test': 'LiveKit SIP outbound calling',
                'timestamp': str(asyncio.get_event_loop().time())
            },
            db=db
        )
        
        print('=' * 70)
        print('✅ CALL INITIATED SUCCESSFULLY!')
        print('=' * 70)
        print()
        print(f'Communication ID: {result["communication_id"]}')
        print(f'Room Name: {result["room_name"]}')
        print(f'SIP Participant ID: {result["sip_participant_id"]}')
        print(f'Status: {result["status"]}')
        print()
        print('🔔 YOUR PHONE SHOULD BE RINGING!')
        print('   Answer to hear the AI agent')
        print()
        print('=' * 70)
        
    except Exception as e:
        print('=' * 70)
        print('❌ ERROR')
        print('=' * 70)
        print()
        print(f'Error: {e}')
        print()
        print('Troubleshooting:')
        print('1. Check LIVEKIT_SIP_TRUNK_ID in .env')
        print('2. Verify SIP trunk exists in LiveKit console')
        print('3. Check LiveKit console for error logs')
        print()
    
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(test_livekit_outbound())
