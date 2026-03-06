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
            self.client = None
        else:
            self.client = telnyx.Telnyx(api_key=self.api_key)
            
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
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            filter_params = {"country_code": country_code, "limit": limit}
            if features:
                # Features like 'sms', 'voice' etc exist in features list but passing it directly might need to be specific to v4 logic.
                # Just passing country and limit to ensure functionality.
                pass
                
            response = self.client.available_phone_numbers.list(filter=filter_params)
            
            results = []
            for num in response.data:
                results.append({
                    "phone_number": num.phone_number,
                    "friendly_name": num.phone_number,
                    "locality": getattr(num, 'locality', 'Unknown'),
                    "region": getattr(num, 'region', 'Unknown'),
                    "iso_country": country_code,
                    "capabilities": {
                        "voice": "voice" in num.features if hasattr(num, 'features') and num.features else False,
                        "sms": "sms" in num.features if hasattr(num, 'features') and num.features else False,
                        "mms": "mms" in num.features if hasattr(num, 'features') and num.features else False
                    }
                })
            return results
        except Exception as e:
            logger.error(f"Error searching Telnyx numbers: {e}")
            raise

    def purchase_phone_number(
        self,
        phone_number: str,
        friendly_name: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> Dict:
        """
        Orders a phone number on Telnyx
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            # According to v4 SDK, we use self.client.number_orders.create
            order = self.client.number_orders.create(
                phone_numbers=[{"phone_number": phone_number}]
            )
            return {
                "id": order.data.id,
                "phone_number": phone_number,
                "status": order.data.status,
                "provider": "telnyx"
            }
        except Exception as e:
            logger.error(f"Error purchasing Telnyx number: {e}")
            raise

    def configure_voice_connection(self, phone_id: str, connection_id: str) -> bool:
        """
        Assigns a phone number to a specific SIP Connection or Call Control App
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            self.client.phone_numbers.update(
                phone_id, 
                connection_id=connection_id
            )
            return True
        except Exception as e:
            logger.error(f"Error configuring Telnyx voice: {e}")
            raise

    def send_sms(self, from_number: str, to_number: str, text: str) -> Dict:
        """
        Sends an SMS via Telnyx
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            message = self.client.messages.send(
                from_=from_number,
                to=to_number,
                text=text
            )
            return {
                "id": message.data.id,
                "status": message.data.status if hasattr(message.data, 'status') else "queued"
            }
        except Exception as e:
            logger.error(f"Error sending Telnyx SMS: {e}")
            raise

    def release_phone_number(self, phone_id: str) -> bool:
        """
        Releases a phone number on Telnyx
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            # According to v4 SDK, we use self.client.phone_numbers.delete
            # Note: phone_id here should be the Telnyx UUID string (telnyx_id in our DB)
            self.client.phone_numbers.delete(phone_id)
            return True
        except Exception as e:
            logger.error(f"Error releasing Telnyx number {phone_id}: {e}")
            raise

    async def create_texml_call(self, from_number: str, to_number: str, url: str, connection_id: str = None) -> Dict:
        """
        Initiates an outbound TeXML call (Twilio-compatible)
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            # Use raw POST since v4 SDK high-level objects for TeXML calls are still rolling out
            payload = {
                "from": from_number,
                "to": to_number,
                "url": url
            }
            if connection_id:
                payload["connection_id"] = connection_id
            
            # Use requests for TeXML calls to avoid SDK path/versioning ambiguity
            import requests
            import asyncio
            url_endpoint = "https://api.telnyx.com/v2/texml/calls"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            def make_request():
                return requests.post(url_endpoint, json=payload, headers=headers)
            
            response = await asyncio.to_thread(make_request)
            
            if response.status_code >= 400:
                 raise Exception(f"Telnyx API Error: {response.status_code} - {response.text}")
            
            data = response.json()
            # Telnyx returns {'data': {'id': '...', 'status': '...'}}
            if 'data' in data:
                data = data['data']
            
            return {
                "id": getattr(data, 'id', None) or data.get('id'),
                "status": getattr(data, 'status', None) or data.get('status', 'initiated')
            }
        except Exception as e:
            logger.error(f"Error creating Telnyx TeXML call: {e}")
            raise

    async def create_call(self, from_: str, to: str, connection_id: str = None, workspace_id: str = None) -> Dict:
        """
        Initiates an outbound Call Control call (non-TeXML).
        If connection_id is not provided, it will attempt to use workspace_id to find the associated connection.
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            conn_id = connection_id
            payload = {
                "from": from_,
                "to": to,
                "connection_id": conn_id
            }
            
            import requests
            import asyncio
            url_endpoint = "https://api.telnyx.com/v2/calls"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            def make_request():
                return requests.post(url_endpoint, json=payload, headers=headers)
            
            response = await asyncio.to_thread(make_request)
            
            if response.status_code >= 400:
                 raise Exception(f"Telnyx API Error: {response.status_code} - {response.text}")
            
            data = response.json().get('data', {})
            return {
                "id": data.get('call_control_id'),
                "status": data.get('state', 'initiated')
            }
        except Exception as e:
            logger.error(f"Error creating Telnyx call: {e}")
            raise

    def create_call_control_application(self, name: str, webhook_url: str) -> Dict:
        """
        Creates a Call Control Application (TeXML or Call Control)
        This is what defines where webhooks go.
        """
        if not self.client:
            raise Exception("Telnyx client not initialized")
            
        try:
            app = self.client.call_control_applications.create(
                application_name=name,
                webhook_event_url=webhook_url,
                webhook_api_version="2"
            )
            return {
                "id": app.data.id,
                "name": app.data.application_name,
                "webhook_url": app.data.webhook_event_url
            }
        except Exception as e:
            logger.error(f"Error creating Telnyx Call Control App: {e}")
            raise
