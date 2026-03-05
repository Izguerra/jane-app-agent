#!/bin/bash

# Deploy Asterisk configuration fixes for RTP audio issue
set -e

SERVER="root@147.182.149.234"
REMOTE_DIR="~/supaagent_telephony/backend/asterisk_config"

echo "Deploying RTP and PJSIP configuration files..."

# Copy configuration files to server
scp backend/asterisk_config/rtp.conf "$SERVER:$REMOTE_DIR/"
scp backend/asterisk_config/pjsip.conf "$SERVER:$REMOTE_DIR/"

echo "Copying files to Asterisk container..."

# SSH and deploy to container
ssh "$SERVER" << 'EOF'
# Copy configs to container
docker cp ~/supaagent_telephony/backend/asterisk_config/rtp.conf supaagent_asterisk:/etc/asterisk/rtp.conf
docker cp ~/supaagent_telephony/backend/asterisk_config/pjsip.conf supaagent_asterisk:/etc/asterisk/pjsip.conf

# Reload Asterisk configuration
docker exec supaagent_asterisk asterisk -rx 'module reload res_pjsip.so'
docker exec supaagent_asterisk asterisk -rx 'module reload res_rtp_asterisk.so'

# Show RTP settings to verify
echo "=== RTP Settings ==="
docker exec supaagent_asterisk asterisk -rx 'rtp show settings'

# Show PJSIP endpoints
echo "=== PJSIP Endpoints ==="
docker exec supaagent_asterisk asterisk -rx 'pjsip show endpoints'
EOF

echo "Deployment complete! Make a test call to verify audio."
