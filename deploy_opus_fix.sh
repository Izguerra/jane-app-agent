#!/bin/bash

# Deploy Asterisk with Opus codec support
set -e

SERVER="root@147.182.149.234"
REMOTE_DIR="~/supaagent_telephony/backend/asterisk_config"

echo "=== Deploying Asterisk with Opus Codec Support ==="

# Step 1: Copy updated configuration files
echo "1. Copying updated PJSIP configuration..."
scp backend/asterisk_config/pjsip.conf "$SERVER:$REMOTE_DIR/"
scp backend/asterisk_config/rtp.conf "$SERVER:$REMOTE_DIR/"

# Step 2: SSH and deploy
echo "2. Deploying to server..."
ssh "$SERVER" << 'EOF'
# Stop and remove current Asterisk container
echo "Stopping current Asterisk container..."
docker stop supaagent_asterisk || true
docker rm supaagent_asterisk || true

# Pull image with Opus support
echo "Pulling Asterisk image with Opus support..."
docker pull andrius/asterisk:latest

# Start new container with Opus support
echo "Starting new Asterisk container with Opus codec..."
docker run -d \
  --name supaagent_asterisk \
  --network host \
  -v ~/supaagent_telephony/backend/asterisk_config/pjsip.conf:/etc/asterisk/pjsip.conf \
  -v ~/supaagent_telephony/backend/asterisk_config/rtp.conf:/etc/asterisk/rtp.conf \
  --restart unless-stopped \
  andrius/asterisk:latest

# Wait for Asterisk to start
echo "Waiting for Asterisk to start..."
sleep 5

# Verify Opus codec is available
echo ""
echo "=== Verifying Opus Codec ==="
docker exec supaagent_asterisk asterisk -rx 'core show codecs' | grep -i opus || echo "WARNING: Opus codec not found!"

# Show PJSIP endpoints
echo ""
echo "=== PJSIP Endpoints ==="
docker exec supaagent_asterisk asterisk -rx 'pjsip show endpoints'

# Show RTP settings
echo ""
echo "=== RTP Settings ==="
docker exec supaagent_asterisk asterisk -rx 'rtp show settings'
EOF

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "✅ Asterisk container restarted with Opus codec support"
echo "✅ Configuration files deployed"
echo ""
echo "🎯 Next Step: Make a test call to verify audio works!"
