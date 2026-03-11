---
description: Implementation plan for Meta WhatsApp Business API integration
---

# Meta WhatsApp Business API Integration

## Overview
Integrate with Meta's WhatsApp Business Platform to enable direct WhatsApp messaging without Twilio. This provides better features, lower costs, and official WhatsApp Business verification.

## Meta vs Twilio WhatsApp

| Feature | Meta WhatsApp API | Twilio WhatsApp |
|---------|------------------|-----------------|
| Cost | Free (conversation-based pricing) | $0.005/message |
| Features | Full WhatsApp Business features | Limited |
| Verification | Official green checkmark | No verification |
| Templates | Required for outbound | Not required |
| Setup | More complex | Simpler |

---

## Prerequisites

Based on your screenshots, you need to complete:

### 1. Meta App Setup (In Progress)
✅ App created: "SupaAgent"
✅ App ID: `3937037266586396`
⚠️ Status: **Unpublished**

**Required actions:**
1. ✅ Complete "Engage with customers on Messenger" use case
2. ✅ Complete "Connect with customers through WhatsApp" use case
3. ⚠️ Become a Tech Provider (required for multi-tenant)
4. ⚠️ Add webhook URL
5. ⚠️ Test use cases
6. ⚠️ Publish app

### 2. WhatsApp Business Account
- Create WhatsApp Business Account in Meta Business Manager
- Verify business (requires business documents)
- Add phone number to WhatsApp Business Account
- Get phone number ID

### 3. Meta Business Verification
- Submit business verification documents
- Wait for approval (1-3 days)
- Required for production access

---

## Phase 1: Meta App Configuration

### 1.1 App Settings (From your screenshots)

**Basic Settings:**
- App ID: `3937037266586396`
- App Secret: (from App Settings → Basic)
- Client Token: `d51e24874a3cbd1275e81e674596cb94`

**Advanced Settings:**
- ✅ API Version: v24.0 (keep updated)
- ⚠️ Server IP Allowlist: Add your server IPs
- ⚠️ Domain Manager: Add `aicustomer-support.netlify.app`

### 1.2 WhatsApp Product Setup

**Navigate to:** Dashboard → Add Products → WhatsApp

**Configuration:**
1. **Create WhatsApp Business Account**
   - Link to your Meta Business Manager
   - Add business details

2. **Add Phone Number**
   - Use test number first (provided by Meta)
   - Later: Add your own verified number

3. **Get Credentials**
   - Phone Number ID
   - WhatsApp Business Account ID
   - Access Token (temporary, 24h)
   - System User Access Token (permanent)

### 1.3 Webhook Configuration

**Webhook URL:** `https://aicustomersupport.onrender.com/webhooks/meta-whatsapp`

**Subscribe to events:**
- `messages` - Incoming messages
- `message_status` - Delivery status
- `messaging_handovers` - Handover protocol

**Verify Token:** Generate a random string (store in `.env`)

---

## Phase 2: Backend Implementation

### 2.1 Environment Variables

Add to `.env`:
```bash
# Meta WhatsApp
META_APP_ID=3937037266586396
META_APP_SECRET=your_app_secret
META_VERIFY_TOKEN=your_random_verify_token
META_SYSTEM_USER_TOKEN=your_permanent_token

# WhatsApp Business Account (per workspace)
# These will be stored in database per workspace
```

### 2.2 Install Dependencies

```bash
pip install requests cryptography
```

### 2.3 Create Meta WhatsApp Service

**File:** `backend/services/meta_whatsapp_service.py`

```python
import requests
import hmac
import hashlib
from typing import Dict, List

class MetaWhatsAppService:
    BASE_URL = "https://graph.facebook.com/v24.0"
    
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
    
    def send_message(self, to: str, message: str) -> Dict:
        """Send text message"""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def send_template(self, to: str, template_name: str, 
                     language_code: str = "en", 
                     components: List = None) -> Dict:
        """Send template message (required for outbound)"""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def mark_as_read(self, message_id: str):
        """Mark message as read"""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        requests.post(url, headers=headers, json=data)
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, 
                                 app_secret: str) -> bool:
        """Verify webhook signature from Meta"""
        expected_signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
```

### 2.4 Create Webhook Handler

**File:** `backend/routers/meta_webhooks.py`

```python
from fastapi import APIRouter, Request, Response, HTTPException
import os
import json
import logging

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
APP_SECRET = os.getenv("META_APP_SECRET")

@router.get("/meta-whatsapp")
async def verify_webhook(request: Request):
    """Webhook verification (Meta will call this)"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta-whatsapp")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages from Meta"""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    
    if not MetaWhatsAppService.verify_webhook_signature(
        body, signature, APP_SECRET
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    data = json.loads(body)
    logger.info(f"Webhook received: {data}")
    
    # Process webhook
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            
            # Handle incoming message
            if "messages" in value:
                for message in value["messages"]:
                    await process_incoming_message(
                        message,
                        value.get("metadata", {})
                    )
            
            # Handle message status
            if "statuses" in value:
                for status in value["statuses"]:
                    await process_message_status(status)
    
    return {"status": "ok"}

async def process_incoming_message(message: dict, metadata: dict):
    """Process incoming WhatsApp message"""
    from backend.database import SessionLocal
    from backend.models_db import Integration, Workspace
    from backend.services import get_agent_manager
    from backend.services.conversation_history import ConversationHistoryService
    
    phone_number_id = metadata.get("phone_number_id")
    from_number = message.get("from")
    message_type = message.get("type")
    message_id = message.get("id")
    
    # Get message content
    if message_type == "text":
        text = message.get("text", {}).get("body", "")
    else:
        # Handle other types (image, audio, etc.)
        text = f"[{message_type} message received]"
    
    # Find workspace by phone_number_id
    db = SessionLocal()
    try:
        integration = db.query(Integration).filter(
            Integration.provider == "meta_whatsapp",
            Integration.settings.contains(f'"phone_number_id":"{phone_number_id}"')
        ).first()
        
        if not integration:
            logger.error(f"No integration found for {phone_number_id}")
            return
        
        workspace_id = integration.workspace_id
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id
        ).first()
        
        # Get conversation history
        history = ConversationHistoryService.get_recent_history(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            limit=10,
            hours=24
        )
        
        # Add user message to history
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            role="user",
            content=text
        )
        
        # Get AI response
        agent_manager = get_agent_manager()
        ai_response = agent_manager.chat(
            text,
            team_id=workspace.team_id,
            workspace_id=workspace_id,
            history=history
        )
        
        # Send response via Meta WhatsApp
        settings = json.loads(integration.settings)
        access_token = settings.get("access_token")
        
        service = MetaWhatsAppService(access_token, phone_number_id)
        service.send_message(from_number, ai_response)
        service.mark_as_read(message_id)
        
        # Store AI response in history
        ConversationHistoryService.add_message(
            workspace_id=workspace_id,
            user_identifier=from_number,
            channel="whatsapp",
            role="assistant",
            content=ai_response
        )
        
    finally:
        db.close()

async def process_message_status(status: dict):
    """Process message delivery status"""
    message_id = status.get("id")
    status_type = status.get("status")  # sent, delivered, read, failed
    
    logger.info(f"Message {message_id} status: {status_type}")
    # Update message status in database if needed
```

---

## Phase 3: Database Schema

### 3.1 Update Integration Model

The existing `Integration` model can store Meta WhatsApp credentials:

```python
# Example settings JSON
{
    "provider": "meta_whatsapp",
    "phone_number_id": "123456789",
    "whatsapp_business_account_id": "987654321",
    "access_token": "permanent_system_user_token",
    "phone_number": "+1234567890"
}
```

### 3.2 Message Templates Table

Create `backend/models_db.py`:

```python
class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    name = Column(String, nullable=False)
    language = Column(String, default="en")
    category = Column(String)  # MARKETING, UTILITY, AUTHENTICATION
    status = Column(String)  # PENDING, APPROVED, REJECTED
    template_id = Column(String)  # Meta template ID
    components = Column(JSON)  # Template structure
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Phase 4: Frontend Integration

### 4.1 Meta WhatsApp Settings Page

**Location:** `app/(dashboard)/dashboard/integrations/page.tsx`

**Add Meta WhatsApp Card:**

```tsx
{
  id: 'meta-whatsapp',
  name: 'WhatsApp (Meta)',
  description: 'Official WhatsApp Business API',
  icon: <MessageSquare className="h-6 w-6" />,
  status: integration?.provider === 'meta_whatsapp' ? 'connected' : 'disconnected',
  fields: [
    {
      name: 'phone_number_id',
      label: 'Phone Number ID',
      type: 'text',
      required: true,
      placeholder: '123456789'
    },
    {
      name: 'whatsapp_business_account_id',
      label: 'Business Account ID',
      type: 'text',
      required: true
    },
    {
      name: 'access_token',
      label: 'System User Access Token',
      type: 'password',
      required: true
    },
    {
      name: 'phone_number',
      label: 'Phone Number',
      type: 'tel',
      placeholder: '+1234567890'
    }
  ]
}
```

### 4.2 Template Management UI

Create `app/(dashboard)/dashboard/whatsapp-templates/page.tsx`:

**Features:**
- List approved templates
- Create new template
- Submit for approval
- View template status
- Test template

---

## Phase 5: Message Templates

### 5.1 Why Templates?

Meta WhatsApp requires **approved templates** for:
- First message to user (24h window)
- Marketing messages
- Notifications

**After user replies**, you have a 24-hour window to send free-form messages.

### 5.2 Create Template via API

```python
def create_template(
    waba_id: str,
    access_token: str,
    name: str,
    category: str,
    language: str,
    components: list
):
    url = f"https://graph.facebook.com/v24.0/{waba_id}/message_templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "category": category,
        "language": language,
        "components": components
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### 5.3 Example Templates

**Appointment Reminder:**
```json
{
  "name": "appointment_reminder",
  "category": "UTILITY",
  "language": "en",
  "components": [
    {
      "type": "BODY",
      "text": "Hi {{1}}, this is a reminder about your appointment on {{2}} at {{3}}. Reply to confirm or reschedule."
    }
  ]
}
```

---

## Phase 6: Multi-Tenant Setup

### 6.1 Become a Tech Provider

**Required for multi-tenant (multiple businesses):**

1. Go to App Dashboard → "Become a Tech Provider"
2. Submit application
3. Wait for approval (1-2 weeks)

**Benefits:**
- Manage multiple WhatsApp Business Accounts
- Embedded signup flow for customers
- Centralized billing

### 6.2 Embedded Signup

Allow customers to connect their own WhatsApp:

```tsx
// Frontend: Trigger Meta signup flow
const handleMetaSignup = () => {
  const url = `https://www.facebook.com/v24.0/dialog/oauth?
    client_id=${META_APP_ID}&
    redirect_uri=${encodeURIComponent(REDIRECT_URI)}&
    state=${workspaceId}&
    scope=whatsapp_business_management,whatsapp_business_messaging`;
  
  window.location.href = url;
};
```

---

## Phase 7: Testing

### 7.1 Test Phone Numbers

Meta provides test numbers:
- No approval needed
- Free messages
- Full API access

**Get test number:**
1. Go to WhatsApp → API Setup
2. Use provided test number
3. Send test message from your phone

### 7.2 Testing Checklist

- [ ] Webhook verification
- [ ] Receive incoming message
- [ ] Send text message
- [ ] Send template message
- [ ] Mark message as read
- [ ] Handle message status updates
- [ ] Test 24-hour window
- [ ] Test multi-workspace isolation

---

## Phase 8: Production Deployment

### 8.1 Business Verification

**Required documents:**
- Business registration
- Tax ID
- Business address
- Website

**Process:**
1. Submit in Meta Business Manager
2. Wait 1-3 days for review
3. Get verified badge

### 8.2 Phone Number Verification

**Options:**
1. **Buy from Meta** (~$0/month, conversation-based pricing)
2. **Use existing number** (requires verification)

**Verification process:**
1. Add phone number in WhatsApp Manager
2. Receive verification code via SMS/call
3. Enter code
4. Wait for approval

### 8.3 App Review & Publishing

**Before publishing:**
- [ ] Complete all use cases
- [ ] Test thoroughly
- [ ] Add privacy policy URL
- [ ] Add terms of service URL
- [ ] Configure data deletion callback
- [ ] Add app icon

**Publish:**
1. Go to App Dashboard → Publish
2. Submit for review
3. Wait for approval (1-3 days)

---

## Pricing Comparison

### Meta WhatsApp (Conversation-based)
- **Free:** User-initiated conversations (24h)
- **Paid:** Business-initiated conversations
  - Marketing: $0.0275/conversation
  - Utility: $0.0055/conversation
  - Authentication: $0.0025/conversation
- **No monthly fees**

### Twilio WhatsApp
- **$0.005/message** (inbound + outbound)
- **$1.15/month** per number

**Example (1000 messages/month):**
- Meta: ~$5-10 (depends on conversation type)
- Twilio: ~$6.15

---

## Security & Compliance

### 1. Webhook Signature Verification
Always verify `X-Hub-Signature-256` header

### 2. Access Token Security
- Use System User tokens (permanent)
- Store encrypted in database
- Never expose in frontend

### 3. Data Privacy
- Implement data deletion callback
- Handle user opt-outs
- Comply with GDPR/CCPA

### 4. Rate Limiting
- Meta limits: 80 messages/second per phone number
- Implement queue for high volume

---

## Timeline

- **Phase 1 (Meta App Setup):** 1-2 days
- **Phase 2 (Backend):** 2-3 days
- **Phase 3 (Database):** 1 day
- **Phase 4 (Frontend):** 2 days
- **Phase 5 (Templates):** 1 day
- **Phase 6 (Multi-tenant):** Wait for approval (1-2 weeks)
- **Phase 7 (Testing):** 1-2 days
- **Phase 8 (Production):** Wait for verification (1-3 days)

**Total development: ~10-12 days**
**Total with approvals: ~3-4 weeks**

---

## Next Steps

### Immediate Actions:

1. **Complete Meta App Setup:**
   - [ ] Add webhook URL in Meta Dashboard
   - [ ] Subscribe to webhook events
   - [ ] Get test phone number
   - [ ] Test webhook with test number

2. **Get Credentials:**
   - [ ] Copy App ID (you have this)
   - [ ] Copy App Secret
   - [ ] Generate System User Access Token
   - [ ] Get Phone Number ID

3. **Start Development:**
   - [ ] Implement webhook handler (Phase 2)
   - [ ] Test with Meta test number
   - [ ] Add frontend UI (Phase 4)

4. **Submit for Approval:**
   - [ ] Apply to become Tech Provider
   - [ ] Submit business verification
   - [ ] Publish app

Would you like me to start implementing Phase 2 (Backend webhook handler)?
