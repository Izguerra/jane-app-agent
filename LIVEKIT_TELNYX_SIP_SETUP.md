# LiveKit Native SIP + Telnyx Direct Integration

## Overview

This setup routes Telnyx inbound phone calls **directly** to LiveKit Cloud's SIP endpoint,
bypassing Asterisk for standard calls. Asterisk remains available for enterprise PBX integrations.

```
STANDARD CALLS:   Phone → Telnyx SIP Connection → LiveKit Cloud SIP → Voice Agent
ENTERPRISE PBX:   Cisco/Avaya/FreePBX → Asterisk (147.182.149.234) → LiveKit Cloud SIP → Voice Agent
```

## Why Not Asterisk for Telnyx?

Telnyx's Call Control API `/v2/calls/{id}/actions/transfer` **mangles SIP URIs**.
When we send `sip:inbound-comm-xxx@asterisk`, Telnyx transforms the room name into a
phone-number-like format (e.g., `00008421232141564`). This causes:
- Asterisk routes to wrong room names
- LiveKit can't match the call to any room
- Voice Agent waits forever for a participant that never arrives

## Setup Instructions

### Step 1: LiveKit Cloud Dashboard

1. Go to **https://cloud.livekit.io** → your project (`jane-clinic-app-tupihomh`)
2. Navigate to **Telephony** → **SIP Trunks**
3. Click **"Create new trunk"**
   - **Name**: `Telnyx Inbound`
   - **Direction**: Inbound  
   - **Numbers**: Add your Telnyx phone number(s) (e.g., `+18382061295`)
   - Save and note your **SIP Endpoint** (e.g., `jane-clinic-app-tupihomh.sip.livekit.cloud`)

4. Navigate to **Telephony** → **Dispatch Rules**
5. Click **"Create new dispatch rule"**
   - **Type**: Individual Room (creates a unique room per call)
   - **Room Prefix**: `sip-call-`
   - **Agent**: Select `supaagent-voice-agent-v2`
   - **Trunk IDs**: Select the trunk you just created
   - Save

### Step 2: Telnyx Mission Control Portal

1. Go to **https://portal.telnyx.com** → **Voice** → **SIP Trunking** → **SIP Connections**
2. Click **"Add SIP Connection"**
   - **Connection Name**: `LiveKit Direct`
   - **Connection Type**: Select **FQDN**
   - **FQDN**: Enter your LiveKit SIP endpoint: `jane-clinic-app-tupihomh.sip.livekit.cloud`
   - **Port**: `5060`
   - **Transport**: `UDP`
   - Save

3. Go to **Numbers** → find your phone number
4. **Re-associate** the number:
   - **Voice Connection**: Select `LiveKit Direct` (the SIP connection you just created)
   - This redirects inbound calls from the Call Control webhook to the direct SIP route
   - Save

### Step 3: Verify

1. Call your Telnyx number from your phone
2. Check `voice_agent.log` — you should see:
   ```
   SIP resolution: callTo=+18382061295, callFrom=+1XXXXXXXXXX
   SIP: Matched phone '+18382061295' → workspace=wrk_xxx, agent=agnt_xxx
   ```
3. The agent should answer and greet you within 2-3 seconds

## Troubleshooting

### Agent doesn't answer
- Check LiveKit Dashboard → **Telephony** → **Call Logs** for SIP errors
- Verify the phone number is added to the Inbound SIP Trunk's number list
- Verify the Dispatch Rule references the correct trunk and agent name

### Wrong agent answers  
- Check the `phone_numbers` table: the `agent_id` column must match the desired agent
- Update via: `UPDATE phone_numbers SET agent_id = 'agnt_xxx' WHERE phone_number = '+18382061295'`

### Asterisk still needed?
Asterisk at `147.182.149.234` is still running and configured for enterprise PBX integrations.
To route a PBX system through Asterisk:
1. Point the PBX's SIP trunk to `147.182.149.234:5060`
2. Asterisk will route to LiveKit via `PJSIP/${ROOM_NAME}@livekit`
3. The Voice Agent will handle the call as usual

## Architecture Notes

- **Voice Agent** uses `VoiceContextResolver._resolve_from_sip()` to look up workspace/agent
  from the dialed phone number's `sip.callTo` attribute
- **Communication records** are still created by the Telnyx Call Control webhook (for SMS/analytics)
  or by the Voice Agent itself when metadata is missing
- **Asterisk** can be enhanced later with Telnyx SIP trunking for enterprise integrations
