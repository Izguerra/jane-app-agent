#!/bin/bash
# redeploy_asterisk_container.sh
# Stops the old container and runs a new one with CORRECT RTP PORTS

echo "========================================================="
echo "   RE-DEPLOYING ASTERISK CONTAINER WITH RTP PORTS"
echo "========================================================="

# 1. Stop and remove existing container
echo "Stopping existing container..."
ssh root@147.182.149.234 "docker stop supaagent_asterisk || true"
ssh root@147.182.149.234 "docker rm supaagent_asterisk || true"

# 2. Run new container with RTP ports (10000-20000/udp) exposed
echo "Starting NEW container..."
# Using --network host is often best for SIP, but if using bridge:
ssh root@147.182.149.234 "docker run -d --name supaagent_asterisk --restart unless-stopped --net=host -v /etc/localtime:/etc/localtime:ro --volume /root/asterisk_config:/etc/asterisk andrius/asterisk"

echo "✅ New container started (using host networking for best SIP compatibility)"
echo ""

# 3. Deploy Configs (Using the existing deployment script logic manually here to be safe)
echo "Deploying Configuration..."
# Extensions
cat backend/asterisk_config/extensions.conf | ssh root@147.182.149.234 "docker exec -i supaagent_asterisk sh -c 'cat > /etc/asterisk/extensions.conf'"
# PJSIP
cat backend/asterisk_config/pjsip_complete.conf | ssh root@147.182.149.234 "docker exec -i supaagent_asterisk sh -c 'cat > /etc/asterisk/pjsip.conf'"

echo "✅ Configuration Deployed"

# 4. Reload
echo "Reloading Asterisk..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'module reload res_pjsip.so'"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan reload'"

echo "========================================================="
echo "   DEPLOYMENT COMPLETE - RTP PORTS SHOULD WORK NOW"
echo "========================================================="
