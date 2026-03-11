#!/bin/bash
# Deploy Asterisk configuration for LiveKit outbound calling

echo "=========================================================================="
echo "Deploying Asterisk Configuration for LiveKit Outbound Calling"
echo "=========================================================================="
echo ""

# Step 1: Deploy extensions.conf
# Step 1: Deploy extensions.conf
# Step 1: Deploy extensions.conf
echo "Step 1: Deploying extensions.conf..."
cat backend/asterisk_config/extensions.conf | ssh root@147.182.149.234 "docker exec -u 0 -i supaagent_asterisk sh -c 'cat > /etc/asterisk/extensions.conf'"
echo "✅ Extensions deployed"
echo ""

# Step 2: Deploy pjsip.conf
echo "Step 2: Deploying pjsip.conf..."
cat backend/asterisk_config/pjsip_complete.conf | ssh root@147.182.149.234 "docker exec -u 0 -i supaagent_asterisk sh -c 'cat > /etc/asterisk/pjsip.conf'"
echo "✅ PJSIP deployed"
echo ""

# Step 3: Reload Asterisk
echo "Step 3: Reloading Asterisk..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan reload'"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'pjsip reload'"
echo "✅ Asterisk reloaded"
echo ""

# Step 4: Verify configuration
echo "Step 4: Verifying configuration..."
echo "Checking from-livekit context..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan show from-livekit'"
echo ""

echo "=========================================================================="
echo "✅ Deployment Complete!"
echo "=========================================================================="
echo ""
echo "Now test with: python3 test_livekit_outbound.py"
echo ""
