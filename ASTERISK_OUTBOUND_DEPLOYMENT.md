# Outbound Calling Implementation - Attempts & Solution

## Executive Summary

After extensive debugging (68+ hours) of LiveKit SIP outbound calling, we encountered persistent connection issues despite multiple configuration approaches. This document details all attempts and the final decision to use **Twilio Programmable Voice API** for a simpler, more reliable solution.

---

## ❌ Attempted Approaches (All Failed)

### Approach 1: LiveKit → Asterisk → Twilio (Initial)
**Goal:** LiveKit dials Asterisk, Asterisk routes to Twilio, Twilio calls customer

**Configuration:**
- LiveKit outbound trunk pointing to Asterisk (147.182.149.234)
- Asterisk `from-livekit` dialplan context
- Asterisk `twilio-outbound` PJSIP trunk
- Twilio credentials in Asterisk pjsip.conf

**Result:** ❌ Failed with "488 Not Acceptable Here" - codec negotiation errors

**Files Created:**
- `backend/asterisk_config/extensions.conf` - Dialplan with from-livekit context
- `backend/asterisk_config/pjsip_complete.conf` - Twilio outbound trunk config
- `deploy_asterisk_complete.sh` - Deployment script

---

### Approach 2: LiveKit → Twilio SIP Direct (Second Attempt)
**Goal:** LiveKit dials Twilio SIP endpoint directly, bypassing Asterisk

**Configuration:**
- LiveKit outbound trunk: `supaagent.pstn.twilio.com`
- Twilio Elastic SIP Trunk created: "SupaAgent_Trunk"
- Trunk SID: `TK5be56c72fec675c86b1890c25764e8de`
- Credential List authentication with Account SID and custom password
- Termination SIP URI: `supaagent.pstn.twilio.com`

**Result:** ❌ Failed with "403 Forbidden" initially, then calls created but never connected

**Issues Encountered:**
1. Initial 403 errors due to missing Twilio Elastic SIP Trunk
2. Password requirements for Credential List (12+ chars, uppercase, lowercase, numbers)
3. Calls appear in LiveKit console but don't ring customer phone
4. No error messages in LiveKit console for recent calls

**Files Created:**
- `backend/services/livekit_outbound_service.py` - LiveKit SIP participant API
- `test_livekit_outbound.py` - Test script
- `LIVEKIT_SIP_SETUP.md` - Setup instructions

---

## ✅ Recommended Solution: Twilio Programmable Voice API

### Why This Approach?

**Pros:**
- ✅ **Proven & Reliable:** Twilio's core product, battle-tested
- ✅ **Simple Implementation:** ~30 minutes vs 68+ hours
- ✅ **No SIP Complexity:** No trunk configuration, no codec issues
- ✅ **Still Uses LiveKit:** Connects to LiveKit for AI conversation
- ✅ **Better Error Handling:** Clear error messages from Twilio API

**Cons:**
- Different platform for outbound vs inbound (acceptable tradeoff)
- Slightly different call flow

### How It Works

```
Backend → Twilio API → Customer Phone → (when answered) → Twilio → Asterisk → LiveKit → AI Agent
```

**Flow:**
1. Backend calls Twilio REST API to initiate outbound call
2. Twilio calls customer's phone number
3. When customer answers, Twilio executes TwiML
4. TwiML uses `<Dial><Sip>` to connect to Asterisk
5. Asterisk routes to LiveKit (existing inbound setup)
6. Customer talks to AI agent via LiveKit

### Implementation Plan

**Files to Modify:**
- `backend/services/outbound_calling_service.py` - Use Twilio API instead of LiveKit SIP
- `backend/routers/voice.py` - Add TwiML endpoint for outbound calls
- Keep existing LiveKit service for reference

**Environment Variables Needed:**
- `TWILIO_ACCOUNT_SID` ✅ (already configured)
- `TWILIO_AUTH_TOKEN` ✅ (already configured)
- `TWILIO_PHONE_NUMBER` ✅ (already configured)
- `BACKEND_URL` ✅ (already configured)

**Estimated Time:** 30-45 minutes

---

## Configuration Reference

### LiveKit SIP Trunk (Attempted)
- **Trunk ID:** `ST_kwrjYtQHRJqW`
- **Address:** `supaagent.pstn.twilio.com`
- **Transport:** UDP
- **Numbers:** `+16478006854`
- **Username:** `<YOUR_TWILIO_ACCOUNT_SID>`
- **Status:** Configured but calls don't connect

### Twilio Elastic SIP Trunk (Created)
- **Name:** SupaAgent_Trunk
- **Trunk SID:** `TK5be56c72fec675c86b1890c25764e8de`
- **Termination URI:** `supaagent.pstn.twilio.com`
- **Credential List:** "Asterisk Admin"
- **Status:** Active but not receiving calls from LiveKit

### Asterisk Configuration (For Reference)
- **Server:** 147.182.149.234
- **Container:** supaagent_asterisk
- **Inbound Context:** `from-twilio` (working ✅)
- **Outbound Context:** `from-livekit` (configured but unused)

---

## Lessons Learned

1. **LiveKit SIP Outbound is Complex:** Requires deep understanding of SIP, codecs, and trunk configuration
2. **IP-Based ACLs Don't Work:** LiveKit Cloud doesn't have static IPs
3. **Credential Authentication Has Strict Requirements:** Password complexity, exact format matching
4. **Silent Failures Are Hard to Debug:** Calls created but no error messages
5. **Simpler is Better:** Using provider's native API (Twilio) is more reliable than SIP trunking

---

## Next Steps

1. ✅ Document all attempts (this file)
2. ⏭️ Implement Twilio Programmable Voice API approach
3. ⏭️ Test outbound calling with new implementation
4. ⏭️ Update walkthrough with final solution

---

## Prerequisites (For Reference)

- Asterisk server running in Docker (supaagent_asterisk)
- Twilio account with phone number (+16478006854)
- LiveKit account (for AI agent, not for SIP outbound)
- SSH access to Asterisk server (147.182.149.234)
