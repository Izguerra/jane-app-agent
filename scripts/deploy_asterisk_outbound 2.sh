#!/bin/bash
# Deploy Asterisk outbound calling configuration

echo "Deploying Asterisk outbound calling configuration..."

# Copy extensions.conf to Asterisk server
echo "1. Copying extensions.conf..."
cat backend/asterisk_config/extensions.conf | ssh root@147.182.149.234 "cat > ~/supaagent_asterisk_extensions.conf"

echo "2. Deploying to Asterisk container..."
ssh root@147.182.149.234 "docker cp ~/supaagent_asterisk_extensions.conf supaagent_asterisk:/etc/asterisk/extensions.conf"

echo "3. Reloading Asterisk dialplan..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan reload'"

echo "4. Verifying dialplan..."
ssh root@147.182.149.234 "docker exec supaagent_asterisk asterisk -rx 'dialplan show from-twilio-outbound'"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test outbound calling with:"
echo "  cd backend && python3 test_outbound_call.py"
