#!/bin/bash
# redeploy_asterisk_container_v2.sh
# Stops the old container and runs a new one with CORRECT RTP PORTS and Bridge Mode

echo "========================================================="
echo "   RE-DEPLOYING ASTERISK WITH EXPLICIT PORTS (V2)"
echo "========================================================="

# 1. Stop and remove existing container
echo "Stopping existing container..."
ssh root@147.182.149.234 "docker stop supaagent_asterisk || true"
ssh root@147.182.149.234 "docker rm supaagent_asterisk || true"

# 2. Run new container with EXPLICIT PORTS
# -p 5060:5060/udp : SIP Signaling
# -p 5060:5060/tcp : SIP Signaling (TCP)
# -p 10000-10099:10000-10099/udp : RTP Audio (reduced range for speed, adjusted in rtp.conf implies standard 10000-20000)
# actually, let's map a smaller range 10000-10200 to be safe and fast, or full range
# Asterisk default rtp.conf usually specifies 10000-20000.
# We will map 10000-10500 to save docker proxy overhead but keep it functional.

echo "Starting NEW container..."
ssh root@147.182.149.234 "docker run -d --name supaagent_asterisk --restart unless-stopped \
  -p 5060:5060/udp \
  -p 5060:5060/tcp \
  -p 10000-10500:10000-10500/udp \
  -v /etc/localtime:/etc/localtime:ro \
  andrius/asterisk"

echo "✅ New container started (Bridge mode with ports 5060 & 10000-10500)"
echo "Waiting 5 seconds for Asterisk to boot..."
sleep 5

# 3. Deploy Configs
echo "Deploying Configuration..."
cat backend/asterisk_config/extensions.conf | ssh root@147.182.149.234 "docker exec -i supaagent_asterisk sh -c 'cat > /etc/asterisk/extensions.conf'"
cat backend/asterisk_config/pjsip_complete.conf | ssh root@147.182.149.234 "docker exec -i supaagent_asterisk sh -c 'cat > /etc/asterisk/pjsip.conf'"

# We also need to configure rtp.conf to match the port range 10000-10500
echo "Configuring rtp.conf..."
ssh root@147.182.149.234 "docker exec -i supaagent_asterisk sh -c 'echo \"[general]\" > /etc/asterisk/rtp.conf && echo \"rtpstart=10000\" >> /etc/asterisk/rtp.conf && echo \"rtpend=10500\" >> /etc/asterisk/rtp.conf'"

echo "✅ Configuration Deployed"

# 4. Reload
echo "Reloading Asterisk..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'module reload res_pjsip.so'"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan reload'"
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'module reload res_rtp_asterisk.so'"

echo "========================================================="
echo "   DEPLOYMENT V2 COMPLETE"
echo "========================================================="
