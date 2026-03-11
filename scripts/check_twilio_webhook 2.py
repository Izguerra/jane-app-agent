import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from backend.database import SessionLocal
from backend.services.integration_service import IntegrationService
from twilio.rest import Client

def check_twilio_webhooks():
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
        print(f"--- Twilio Number Configuration for {phone_number} ---")
        print(f"Voice URL (Inbound Webhook): {number.voice_url}")
        print(f"Voice Method: {number.voice_method}")
        print(f"Status Callback URL: {number.status_callback}")
        print(f"Status Callback Method: {number.status_callback_method}")
        
    except Exception as e:
        print(f"Failed to check Twilio configuration: {e}")

if __name__ == "__main__":
    check_twilio_webhooks()
