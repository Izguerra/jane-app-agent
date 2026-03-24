#!/bin/bash
# ============================================================
# DEPLOY ASTERISK SIP SECURITY FIX
# ============================================================
# This script deploys the hardened pjsip.conf to the Asterisk
# server to block SIP probe scanners.
#
# Run this on the Asterisk server (147.182.149.234):
#   bash deploy_asterisk_fix.sh
#
# Or from your local machine:
#   ssh root@147.182.149.234 "bash -s" < scripts/deploy_asterisk_fix.sh
# ============================================================

set -e

echo "🔒 Deploying Asterisk SIP Security Fix..."

# Backup current config
echo "📦 Backing up current pjsip.conf..."
docker exec supaagent_asterisk cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.bak.$(date +%Y%m%d_%H%M%S)

# Write the hardened pjsip.conf
echo "📝 Writing hardened pjsip.conf..."
docker exec supaagent_asterisk sh -c 'cat > /etc/asterisk/pjsip.conf << "PJSIP_EOF"
[global]
type=global
user_agent=SupaAgent_Gateway

; --- TRANSPORTS ---
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
external_media_address=147.182.149.234
external_signaling_address=147.182.149.234
; SECURITY: Restrict local_net to specific segments
local_net=172.16.0.0/12
local_net=192.168.0.0/16
local_net=10.0.0.0/8

[transport-tcp]
type=transport
protocol=tcp
bind=0.0.0.0:5060
external_media_address=147.182.149.234
external_signaling_address=147.182.149.234
local_net=172.16.0.0/12
local_net=192.168.0.0/16
local_net=10.0.0.0/8

; --- TWILIO/TELNYX TRUNK (INBOUND) ---
[twilio]
type=endpoint
context=from-twilio
disallow=all
allow=opus
allow=ulaw
allow=alaw
direct_media=no
aors=twilio
force_rport=yes
ice_support=yes
rewrite_contact=yes
rtp_symmetric=yes
media_address=147.182.149.234

[twilio]
type=identify
endpoint=twilio
; SECURITY: Restrict to known Telnyx SIP signaling IPs ONLY.
; match=0.0.0.0/0 was the ROOT CAUSE of runaway SIP probe rooms.
; Telnyx US signaling:
match=192.76.120.10
match=64.16.250.10
; Telnyx US network ranges:
match=192.76.120.128/29
match=192.76.120.136/29
match=192.76.120.144/29
match=192.76.120.160/29
; Telnyx Canada:
match=192.76.120.31
match=64.16.250.13
; Telnyx Europe:
match=185.246.41.140
match=185.246.41.141
match=185.246.41.0/29
match=185.246.41.8/29
match=185.246.41.16/29

[twilio]
type=aor
contact=sip:54.172.60.0:5060

; --- LIVEKIT TRUNK (OUTBOUND) ---
[livekit]
type=endpoint
context=default
disallow=all
allow=ulaw
direct_media=no
aors=livekit
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes
media_address=147.182.149.234
send_rpid=yes
trust_id_inbound=yes

[livekit]
type=aor
contact=sip:c54dhff28i8.sip.livekit.cloud

[livekit-auth]
type=auth
auth_type=userpass
username=YOUR_TWILIO_ACCOUNT_SID
password=YOUR_PASSWORD
PJSIP_EOF'

# Write the hardened extensions.conf
echo "📝 Writing hardened extensions.conf..."
docker exec supaagent_asterisk sh -c 'cat > /etc/asterisk/extensions.conf << "EXT_EOF"
; Asterisk Dialplan for LiveKit Outbound Calls
; This handles calls FROM LiveKit TO customer phones via Twilio

; Context for calls coming FROM LiveKit (outbound to customers)
[from-livekit]
exten => _+1NXXNXXXXXX,1,NoOp(Outbound call from LiveKit to ${EXTEN})
same => n,Set(TO_NUMBER=${EXTEN})
same => n,NoOp(Dialing ${TO_NUMBER} via Twilio)
same => n,Dial(PJSIP/${TO_NUMBER}@twilio-outbound,60)
same => n,Hangup()

; Fallback for any other number format
exten => _X.,1,NoOp(Outbound call from LiveKit to ${EXTEN})
same => n,Set(TO_NUMBER=${EXTEN})
same => n,NoOp(Dialing ${TO_NUMBER} via Twilio)
same => n,Dial(PJSIP/${TO_NUMBER}@twilio-outbound,60)
same => n,Hangup()

; Keep existing inbound context
[from-twilio]
; Handle any call to Asterisk (inbound from Telnyx)
exten => _.,1,NoOp(Call to Asterisk: ${EXTEN})
; SECURITY: Validate extension to prevent injection attacks
same => n,Set(VALID_EXTEN=${REGEX("^[a-zA-Z0-9\-\_]+$" ${EXTEN})})
same => n,GotoIf($[${VALID_EXTEN} = 0]?invalid_exten)

; Always try to read the X-LiveKit-Room header sent by Telnyx transfer first
same => n,Set(ROOM_NAME=${PJSIP_HEADER(read,X-LiveKit-Room)})
same => n,GotoIf($[${LEN(${ROOM_NAME})} > 0]?has_room)
same => n,Set(ROOM_NAME=${EXTEN})
same => n(has_room),NoOp(Room Name dynamically resolved to: ${ROOM_NAME})
; Try to read metadata if present in SIP headers
same => n,Set(__ROOM_METADATA=${PJSIP_HEADER(read,X-Room-Metadata)})
same => n,Log(NOTICE, Bridging call to LiveKit Room: ${ROOM_NAME})
same => n,Answer()
same => n,Wait(1)
; Use pre-dial handler for ALL calls to LiveKit
same => n,Dial(PJSIP/${ROOM_NAME}@livekit,60,b(add_metadata^add_header^1))
same => n,Hangup()

; Error handling for invalid extension - SECURITY: Do not Answer()
same => n(invalid_exten),Log(WARNING, ALERT: Rejected malicious extension: ${EXTEN})
same => n,Hangup(21)

; Pre-dial handler to add headers to outgoing channel
[add_metadata]
exten => add_header,1,NoOp(Adding SIP Headers for LiveKit)
same => n,Set(PJSIP_HEADER(add,X-LiveKit-Room)=${ROOM_NAME})
same => n,GotoIf($[${LEN(${ROOM_METADATA})} = 0]?skip)
same => n,Set(PJSIP_HEADER(add,X-Room-Metadata)=${ROOM_METADATA})
same => n(skip),Return()
EXT_EOF'

# Reload Asterisk
echo "🔄 Reloading Asterisk configuration..."
docker exec supaagent_asterisk asterisk -rx "core reload"

echo ""
echo "✅ Asterisk SIP security fix deployed!"
echo "   - pjsip.conf: Restricted to Telnyx IPs only"
echo "   - extensions.conf: Hardened with immediate Hangup for invalid extensions"
echo "   - SIP probes from unknown IPs will now be REJECTED at the network level"
echo ""
echo "🔍 Verify with:"
echo "   docker exec supaagent_asterisk asterisk -rx 'pjsip show endpoints'"
echo "   docker exec supaagent_asterisk asterisk -rx 'dialplan show from-twilio'"
