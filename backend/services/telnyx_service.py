"""
Telnyx Phone Number Provisioning and Communication Service

Handles:
- Searching for available phone numbers
- Purchasing phone numbers
- Configuring phone numbers for voice (Call Control / LiveKit SIP)
- Releasing phone numbers
- Sending and receiving SMS
"""

import os
import logging
import telnyx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TelnyxService:
    """Service for managing Telnyx communications"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TELNYX_API_KEY")
        if not self.api_key:
            logger.warning("Telnyx API Key not found. Service may fail for authenticated requests.")
        else:
            telnyx.api_key = self.api_key
            
    def search_phone_numbers(
        self,
        country_code: str = "US",
        area_code: Optional[str] = None,
        limit: int = 20,
        features: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for available phone numbers in Telnyx
        """
        try:
            params = {
                "filter[country_code]": country_code,
                "filter[limit]": limit
            }
            if area_code:
                params["filter[phone_number][contains]"] = area_code
            if features:
                # e.g. ["sms", "voice"]
                params["filter[features]"] = features

            numbers = telnyx.AvailablePhoneNumber.list(**params)
            
            results = []
            for num in numbers:
                results.append({
                    "phone_number": num.phone_number,
                    "friendly_name": num.phone_number, # Telnyx doesn't provide a 'friendly' format always
                    "locality": getattr(num, 'locality', 'Unknown'),
                    "region": getattr(num, 'region', 'Unknown'),
                    "iso_country": country_code,
                    "capabilities": {
                        "voice": "voice" in num.features,
                        "sms": "sms" in num.features,
                        "mms": "mms" in num.features
                    }
                })
            return results
        except Exception as e:
            logger.error(f"Error searching Telnyx numbers: {e}")
            raise

    def purchase_phone_number(
        self,
        phone_number: str,
        workspace_id: str,
        connection_id: Optional[str] = None
    ) -> Dict:
        """
        Orders a phone number on Telnyx
        """
        try:
            order = telnyx.NumberOrder.create(
                phone_numbers=[{"phone_number": phone_number}]
            )
            # Orders are asynchronous in Telnyx, but for basic usage we wait for status
            # In a production app, we should handle the 'number_order.complete' webhook
            
            # For simplicity in this implementation, we assume success or handle it via polling/later config
            return {
                "id": order.id,
                "phone_number": phone_number,
                "status": order.status
            }
        except Exception as e:
            logger.error(f"Error purchasing Telnyx number: {e}")
            raise

    def configure_voice_connection(self, phone_id: str, connection_id: str) -> bool:
        """
        Assigns a phone number to a specific SIP Connection or Call Control App
        """
        try:
            number = telnyx.PhoneNumber.retrieve(phone_id)
            number.connection_id = connection_id
            number.save()
            return True
        except Exception as e:
            logger.error(f"Error configuring Telnyx voice: {e}")
            raise

    def send_sms(self, from_number: str, to_number: str, text: str) -> Dict:
        """
        Sends an SMS via Telnyx
        """
        try:
            message = telnyx.Message.create(
                from_=from_number,
                to=to_number,
                text=text
            )
            return {
                "id": message.id,
                "status": message.status
            }
        except Exception as e:
            logger.error(f"Error sending Telnyx SMS: {e}")
            raise

    def create_call_control_application(self, name: str, webhook_url: str) -> Dict:
        """
        Creates a Call Control Application (TeXML or Call Control)
        This is what defines where webhooks go.
        """
        try:
            app = telnyx.CallControlApplication.create(
                application_name=name,
                webhook_event_url=webhook_url,
                webhook_api_version="2"
            )
            return {
                "id": app.id,
                "name": app.application_name,
                "webhook_url": app.webhook_event_url
            }
        except Exception as e:
            logger.error(f"Error creating Telnyx Call Control App: {e}")
            raise
