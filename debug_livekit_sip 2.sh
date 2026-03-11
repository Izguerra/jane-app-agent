#!/bin/bash
# Test LiveKit SIP outbound calling step by step

echo "==================================================================="
echo "LiveKit SIP Outbound Call Debugging"
echo "==================================================================="
echo ""

# Step 1: Check if LiveKit SIP trunk is reachable from Asterisk
echo "Step 1: Testing LiveKit SIP trunk connectivity..."
echo "-------------------------------------------------------------------"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'pjsip show endpoints' | grep livekit"
echo ""

# Step 2: Check current Asterisk dialplan
echo "Step 2: Checking Asterisk dialplan for outbound context..."
echo "-------------------------------------------------------------------"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan show from-twilio'"
echo ""

# Step 3: Make a test call and watch Asterisk logs
echo "Step 3: Initiating test call..."
echo "-------------------------------------------------------------------"
cd /Users/randyesguerra/Documents/Projects/JaneAppAgent
backend/venv/bin/python3 << 'PYTHON_EOF'
import os, sys
sys.path.insert(0, '/Users/randyesguerra/Documents/Projects/JaneAppAgent')

with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from backend.services.outbound_calling_service import outbound_calling_service
from backend.database import SessionLocal
from backend.models_db import Workspace

db = SessionLocal()
workspace = db.query(Workspace).first()

result = outbound_calling_service.initiate_call(
    workspace_id=workspace.id,
    to_phone='+14167865786',
    from_phone='+16478006854',
    call_intent='test',
    call_context={'test': 'debug'},
    db=db
)

print(f"Call SID: {result['twilio_call_sid']}")
print(f"Room: outbound_{result['communication_id']}")
db.close()
PYTHON_EOF

echo ""
echo "Step 4: Watching Asterisk logs for 10 seconds..."
echo "-------------------------------------------------------------------"
ssh root@147.182.149.234 "timeout 10 docker logs -f supaagent_asterisk 2>&1 | grep -i 'outbound\|livekit\|dial\|error'" || true

echo ""
echo "==================================================================="
echo "Debug complete!"
echo "==================================================================="
