import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from backend.database import SessionLocal
from backend.services.integration_service import IntegrationService
from twilio.rest import Client

def update_twilio_webhook():
    workspace_id = "wrk_1768318949488"
    account_sid = IntegrationService.get_provider_key(workspace_id, "twilio", "TWILIO_ACCOUNT_SID")
    auth_token = IntegrationService.get_provider_key(workspace_id, "twilio", "TWILIO_AUTH_TOKEN")
    phone_number = IntegrationService.get_provider_key(workspace_id, "twilio", "TWILIO_PHONE_NUMBER")

    if not account_sid or not auth_token:
        print("Error: Twilio credentials not found in database for workspace.")
        return

    try:
        client = Client(account_sid, auth_token)
        numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not numbers:
            print(f"Error: Phone number {phone_number} not found in this Twilio account.")
            return
            
        number = numbers[0]
        
        webhook_url = "https://precoracoid-moonishly-tonda.ngrok-free.dev/phone/webhook"
        
        print(f"Updating Twilio number {phone_number}...")
        print(f"New Voice URL: {webhook_url}")
        
        number = number.update(
            voice_url=webhook_url,
            voice_method='POST'
        )
        
        print("Successfully updated Twilio incoming webhook!")
        print(f"Current Voice URL is now: {number.voice_url}")

    except Exception as e:
        print(f"Failed to update Twilio configuration: {e}")

if __name__ == "__main__":
    update_twilio_webhook()
