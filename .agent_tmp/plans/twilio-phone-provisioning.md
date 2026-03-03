---
description: Implementation plan for Twilio phone number and WhatsApp provisioning
---

# Twilio Phone Number & WhatsApp Provisioning Integration

## Overview
Enable users to purchase and provision Twilio phone numbers (voice and WhatsApp) directly from the SupaAgent dashboard, eliminating manual setup in Twilio Console.

## Goals
1. Allow users to search and purchase Twilio phone numbers
2. Automatically configure phone numbers for voice calls (LiveKit SIP)
3. Automatically configure phone numbers for WhatsApp messaging
4. Store phone number details in workspace settings
5. Handle billing and usage tracking

---

## Phase 1: Twilio API Integration (Backend)

### 1.1 Install Twilio SDK
```bash
pip install twilio
```

Add to `backend/requirements.txt`:
```
twilio>=8.0.0
```

### 1.2 Environment Variables
Add to `.env`:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_API_KEY=your_api_key
TWILIO_API_SECRET=your_api_secret
```

### 1.3 Create Twilio Service (`backend/services/twilio_service.py`)

**Features:**
- Search available phone numbers by area code/country
- Purchase phone numbers
- Configure phone numbers for voice (SIP trunk)
- Configure phone numbers for WhatsApp
- Release phone numbers
- Get phone number details and usage

**Key Methods:**
```python
class TwilioService:
    def search_phone_numbers(country_code, area_code=None, capabilities=None)
    def purchase_phone_number(phone_number, workspace_id)
    def configure_voice_number(phone_number, sip_trunk_url)
    def configure_whatsapp_number(phone_number, webhook_url)
    def release_phone_number(phone_number, workspace_id)
    def get_phone_number_details(phone_number)
    def get_usage_and_cost(workspace_id)
```

### 1.4 Create Phone Number Router (`backend/routers/phone_numbers.py`)

**Endpoints:**
- `GET /phone-numbers/search` - Search available numbers
- `POST /phone-numbers/purchase` - Purchase a number
- `GET /phone-numbers` - List workspace phone numbers
- `DELETE /phone-numbers/{phone_number}` - Release a number
- `PUT /phone-numbers/{phone_number}/configure` - Update configuration
- `GET /phone-numbers/{phone_number}/usage` - Get usage stats

---

## Phase 2: Database Schema Updates

### 2.1 Create PhoneNumber Model (`backend/models_db.py`)

```python
class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    phone_number = Column(String, unique=True, nullable=False)
    friendly_name = Column(String)
    country_code = Column(String(2))
    
    # Capabilities
    voice_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    
    # Configuration
    voice_url = Column(String)  # LiveKit SIP trunk URL
    whatsapp_webhook_url = Column(String)
    
    # Twilio details
    twilio_sid = Column(String, unique=True)
    
    # Billing
    monthly_cost = Column(Float)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### 2.2 Migration Script

Create `migrations/003_add_phone_numbers.sql`:
```sql
CREATE TABLE phone_numbers (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    friendly_name VARCHAR(255),
    country_code VARCHAR(2),
    voice_enabled BOOLEAN DEFAULT FALSE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    voice_url TEXT,
    whatsapp_webhook_url TEXT,
    twilio_sid VARCHAR(255) UNIQUE,
    monthly_cost DECIMAL(10,2),
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phone_numbers_workspace ON phone_numbers(workspace_id);
CREATE INDEX idx_phone_numbers_phone ON phone_numbers(phone_number);
```

---

## Phase 3: Frontend UI (Next.js)

### 3.1 Phone Number Provisioning Page

**Location:** `app/(dashboard)/dashboard/phone-numbers/page.tsx`

**Features:**
- Search for available phone numbers
- Filter by country, area code, capabilities
- Display pricing
- Purchase button with confirmation
- List of owned phone numbers
- Configure/release actions

**Components:**
- `PhoneNumberSearch` - Search and filter interface
- `PhoneNumberCard` - Display available number with purchase button
- `OwnedPhoneNumbers` - Table of workspace phone numbers
- `PhoneNumberConfig` - Modal for configuration

### 3.2 API Routes

Create frontend API proxies:
- `app/api/phone-numbers/search/route.ts`
- `app/api/phone-numbers/purchase/route.ts`
- `app/api/phone-numbers/route.ts` (GET/DELETE)
- `app/api/phone-numbers/[phoneNumber]/route.ts` (PUT)

---

## Phase 4: LiveKit SIP Integration

### 4.1 Automatic SIP Trunk Configuration

When a voice-enabled number is purchased:

1. **Create LiveKit SIP Trunk** (if not exists)
   ```python
   from livekit import api
   
   lk_api = api.LiveKitAPI()
   trunk = lk_api.sip.create_sip_trunk(
       name=f"workspace-{workspace_id}",
       inbound_addresses=["your-livekit-sip-address"],
       outbound_number=phone_number
   )
   ```

2. **Create SIP Inbound Rule**
   ```python
   lk_api.sip.create_sip_inbound_trunk(
       trunk_id=trunk.sip_trunk_id,
       numbers=[phone_number],
       allowed_numbers=["*"],  # Or restrict
       room_name_pattern=f"voice-{workspace_id}-{{callID}}"
   )
   ```

3. **Configure Twilio to forward to LiveKit**
   ```python
   twilio_client.incoming_phone_numbers(phone_sid).update(
       voice_url=f"https://{LIVEKIT_SIP_ADDRESS}/sip/inbound",
       voice_method="POST"
   )
   ```

---

## Phase 5: WhatsApp Configuration

### 5.1 Twilio WhatsApp Setup

When WhatsApp is enabled:

1. **Request WhatsApp enablement** (requires Twilio approval)
   ```python
   # Note: This is usually done via Twilio Console first
   # Then programmatically configure webhook
   ```

2. **Configure webhook**
   ```python
   webhook_url = f"{BACKEND_URL}/webhooks/whatsapp"
   
   twilio_client.incoming_phone_numbers(phone_sid).update(
       sms_url=webhook_url,
       sms_method="POST"
   )
   ```

3. **Update workspace settings**
   ```python
   integration = Integration(
       workspace_id=workspace_id,
       provider="whatsapp",
       settings=json.dumps({
           "phone": phone_number,
           "twilio_sid": phone_sid
       }),
       is_active=True
   )
   ```

---

## Phase 6: Billing & Usage Tracking

### 6.1 Cost Tracking

**Monthly costs:**
- Phone number rental: ~$1-2/month
- Voice minutes: ~$0.01-0.02/min
- WhatsApp messages: ~$0.005/message

**Implementation:**
```python
class UsageTracker:
    def track_voice_call(workspace_id, duration_seconds):
        # Calculate cost based on duration
        # Update workspace.voice_minutes_this_month
        
    def track_whatsapp_message(workspace_id):
        # Increment message count
        # Calculate cost
        
    def get_monthly_bill(workspace_id):
        # Sum all costs for current month
```

### 6.2 Usage Dashboard

Add to analytics page:
- Total phone numbers
- Voice minutes used
- WhatsApp messages sent
- Estimated monthly cost
- Usage trends

---

## Phase 7: Testing & Deployment

### 7.1 Testing Checklist

- [ ] Search phone numbers by country
- [ ] Purchase phone number
- [ ] Configure for voice (test incoming call)
- [ ] Configure for WhatsApp (test incoming message)
- [ ] Release phone number
- [ ] Verify billing calculations
- [ ] Test multi-workspace isolation

### 7.2 Error Handling

**Common errors:**
- Insufficient Twilio balance
- Phone number unavailable
- WhatsApp not approved
- SIP trunk configuration failure
- Webhook delivery failure

**Implementation:**
- Retry logic for transient failures
- Clear error messages to user
- Rollback on partial failures
- Logging for debugging

---

## Security Considerations

1. **Validate workspace ownership** before any phone number operation
2. **Rate limit** phone number purchases (prevent abuse)
3. **Verify Twilio webhooks** using signature validation
4. **Encrypt** Twilio credentials in database
5. **Audit log** all phone number operations

---

## Cost Estimates

**Per workspace:**
- 1 voice number: $1.15/month
- 1 WhatsApp number: $1.15/month (same number can do both)
- Voice usage: Variable ($0.01-0.02/min)
- WhatsApp usage: Variable ($0.005/message)

**Example:**
- 100 workspaces
- 1 phone number each
- 1000 minutes voice/month
- 5000 WhatsApp messages/month
- **Total: ~$165/month**

---

## Timeline

- **Phase 1-2 (Backend):** 2-3 days
- **Phase 3 (Frontend):** 2 days
- **Phase 4 (LiveKit SIP):** 1-2 days
- **Phase 5 (WhatsApp):** 1 day
- **Phase 6 (Billing):** 1 day
- **Phase 7 (Testing):** 1-2 days

**Total: ~10-12 days**

---

## Next Steps

1. Review and approve this plan
2. Set up Twilio account with sufficient balance
3. Configure LiveKit SIP trunk
4. Start with Phase 1 (Backend API)
5. Test with sandbox numbers before production
