# LiveKit SIP Outbound Calling - Setup Instructions

## Prerequisites

Before testing LiveKit SIP outbound calling, you need to configure a SIP trunk in LiveKit.

### Step 1: Get LiveKit SIP Trunk ID

1. Go to LiveKit Cloud Console: https://cloud.livekit.io
2. Navigate to your project: `jane-clinic-app-tupihomh`
3. Go to **Settings** → **SIP**
4. Click **"Create SIP Trunk"** or view existing trunk
5. Copy the **SIP Trunk ID** (looks like: `ST_xxxxxxxxxxxxx`)

### Step 2: Configure SIP Trunk (if not already done)

In the LiveKit SIP settings:
- **Trunk Type**: Outbound
- **SIP Provider**: Your SIP provider (or use LiveKit's default)
- **Authentication**: Configure if required

### Step 3: Add to Environment Variables

Add to `.env`:
```bash
LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxxxxxx
LIVEKIT_SIP_NUMBER=+1234567890  # Your outbound caller ID (optional)
```

### Step 4: Test Outbound Call

Run the test script:
```bash
cd /Users/randyesguerra/Documents/Projects/JaneAppAgent
python3 test_livekit_outbound.py
```

## How It Works

**New Architecture (LiveKit Direct):**
```
Your Backend
  ↓
LiveKit CreateSIPParticipant API
  ↓
LiveKit creates room + dispatches agent
  ↓
LiveKit dials customer via SIP
  ↓
Customer answers
  ↓
AI Agent conversation
```

**Old Architecture (Twilio - doesn't work):**
```
Your Backend → Twilio → Asterisk → LiveKit (failed)
```

## Benefits

1. ✅ **Simpler** - No Twilio or Asterisk needed for outbound
2. ✅ **Free** - 1,000 SIP minutes included in LiveKit free plan
3. ✅ **Direct** - LiveKit handles everything
4. ✅ **Unified** - Same platform for inbound and outbound

## Troubleshooting

### Error: "SIP trunk not found"
- Make sure `LIVEKIT_SIP_TRUNK_ID` is set correctly in `.env`
- Verify the trunk exists in LiveKit console

### Error: "Invalid phone number"
- Phone numbers must be in E.164 format: `+14167865786`
- Service automatically adds `+` if missing

### Call doesn't connect
- Check LiveKit console for call logs
- Verify SIP trunk is configured for outbound calls
- Check that your LiveKit plan includes SIP minutes

## Next Steps

Once working:
1. Update outbound router to use LiveKit service
2. Remove Twilio dependency for outbound calls
3. Add UI button for outbound calling
4. Test end-to-end flow
