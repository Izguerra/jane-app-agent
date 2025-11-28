from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from twilio.rest import Client

router = APIRouter(prefix="/phone", tags=["phone"])

# Initialize Twilio Client
# In production, ensure these env vars are set
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = None

if account_sid and auth_token and account_sid != "placeholder":
    try:
        twilio_client = Client(account_sid, auth_token)
    except Exception as e:
        print(f"Failed to initialize Twilio client: {e}")

class PhoneNumber(BaseModel):
    friendly_name: str
    phone_number: str
    iso_country: str

class BuyPhoneRequest(BaseModel):
    phone_number: str
    area_code: str

@router.get("/search", response_model=List[PhoneNumber])
async def search_phone_numbers(area_code: str = "415", country_code: str = "US"):
    if not twilio_client:
        # Return mock data if Twilio is not configured
        return [
            PhoneNumber(friendly_name="(415) 555-0100", phone_number="+14155550100", iso_country="US"),
            PhoneNumber(friendly_name="(415) 555-0101", phone_number="+14155550101", iso_country="US"),
            PhoneNumber(friendly_name="(415) 555-0102", phone_number="+14155550102", iso_country="US"),
        ]

    try:
        available_numbers = twilio_client.available_phone_numbers(country_code).local.list(
            area_code=area_code,
            limit=5
        )
        return [
            PhoneNumber(
                friendly_name=num.friendly_name,
                phone_number=num.phone_number,
                iso_country=num.iso_country
            ) for num in available_numbers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/buy")
async def buy_phone_number(request: BuyPhoneRequest):
    if not twilio_client:
        return {"status": "success", "message": f"Mock purchase of {request.phone_number}"}

    try:
        # Buy the number
        purchased_number = twilio_client.incoming_phone_numbers.create(
            phone_number=request.phone_number
        )
        
        # Configure the webhook (Voice URL)
        # In production, this should be your actual public URL
        webhook_url = os.getenv("BASE_URL", "https://api.janeagent.com") + "/phone/webhook"
        
        purchased_number.update(
            voice_url=webhook_url,
            voice_method="POST"
        )

        return {"status": "success", "data": {
            "sid": purchased_number.sid,
            "phone_number": purchased_number.phone_number
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def voice_webhook():
    # TwiML response to connect to LiveKit (via SIP or WebSocket)
    # For now, we'll just say a message
    return """
    <?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Connecting you to Jane AI.</Say>
        <Connect>
            <Stream url="wss://your-livekit-server.com" />
        </Connect>
    </Response>
    """
