"""
Twilio Phone Number Provisioning Service

Handles:
- Searching for available phone numbers
- Purchasing phone numbers
- Configuring phone numbers for voice (LiveKit SIP) and WhatsApp
- Releasing phone numbers
- Usage tracking
"""

import os
import logging
from typing import List, Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for managing Twilio phone numbers"""
    
    def __init__(self):
        # Check for Test Credentials first
        self.test_account_sid = os.getenv("TWILIO_TEST_ACCOUNT_SID")
        self.test_auth_token = os.getenv("TWILIO_TEST_AUTH_TOKEN")
        
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if self.test_account_sid and self.test_auth_token:
            logger.warning("USING TWILIO TEST CREDENTIALS - No actual purchases will be made.")
            self.client = Client(self.test_account_sid, self.test_auth_token)
            # We still need the main Account SID for some operations potentially, 
            # but the Client is authenticated with Test Creds.
        elif self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio service initialized with LIVE credentials")
        else:
            raise ValueError("Twilio credentials not found. Set TWILIO_ACCOUNT_SID/TOKEN or TWILIO_TEST_ACCOUNT_SID/TOKEN.")
    
    def search_phone_numbers(
        self,
        country_code: str = "US",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        voice_enabled: bool = True,
        sms_enabled: bool = False,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search for available phone numbers
        
        Args:
            country_code: ISO country code (US, CA, GB, etc.)
            area_code: Area code to search in (e.g., "415" for San Francisco)
            contains: Pattern to search for in phone number
            voice_enabled: Filter for voice capability
            sms_enabled: Filter for SMS capability
            limit: Maximum number of results
            
        Returns:
            List of available phone numbers with details
        """
        try:
            # Handle Test Mode Mocking
            if hasattr(self, 'test_account_sid') and self.test_account_sid:
                logger.info("TEST MODE: Returning Mock Magic Number")
                return [{
                    "phone_number": "+15005550006",
                    "friendly_name": "(500) 555-0006",
                    "locality": "Magic City",
                    "region": "Testland",
                    "postal_code": "00000",
                    "iso_country": "US",
                    "capabilities": {
                        "voice": True,
                        "sms": True,
                        "mms": True
                    }
                }]

            search_params = {
                "limit": limit
            }
            
            if area_code:
                search_params["area_code"] = area_code
            if contains:
                search_params["contains"] = contains
            if voice_enabled:
                search_params["voice_enabled"] = True
            if sms_enabled:
                search_params["sms_enabled"] = True
            
            # Search for local numbers
            available_numbers = self.client.available_phone_numbers(country_code).local.list(
                **search_params
            )
            
            results = []
            for number in available_numbers:
                results.append({
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "locality": number.locality,
                    "region": number.region,
                    "postal_code": number.postal_code,
                    "iso_country": number.iso_country,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("SMS", False),
                        "mms": number.capabilities.get("MMS", False)
                    }
                })
            
            logger.info(f"Found {len(results)} available numbers in {country_code}")
            return results
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error searching numbers: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching phone numbers: {e}")
            raise
    
    def purchase_phone_number(
        self,
        phone_number: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None,
        friendly_name: Optional[str] = None
    ) -> Dict:
        """
        Purchase a phone number
        
        Args:
            phone_number: Phone number to purchase (E.164 format)
            voice_url: Webhook URL for incoming calls
            sms_url: Webhook URL for incoming SMS/WhatsApp
            friendly_name: Custom name for the number
            
        Returns:
            Details of purchased number including SID
        """
        try:
            purchase_params = {
                "phone_number": phone_number
            }
            
            if voice_url:
                purchase_params["voice_url"] = voice_url
                purchase_params["voice_method"] = "POST"
            
            if sms_url:
                purchase_params["sms_url"] = sms_url
                purchase_params["sms_method"] = "POST"
            
            if friendly_name:
                purchase_params["friendly_name"] = friendly_name
            
            # Purchase the number
            incoming_number = self.client.incoming_phone_numbers.create(
                **purchase_params
            )
            
            logger.info(f"Purchased phone number: {phone_number} (SID: {incoming_number.sid})")
            
            return {
                "sid": incoming_number.sid,
                "phone_number": incoming_number.phone_number,
                "friendly_name": incoming_number.friendly_name,
                "capabilities": {
                    "voice": incoming_number.capabilities.get("voice", False),
                    "sms": incoming_number.capabilities.get("SMS", False),
                    "mms": incoming_number.capabilities.get("MMS", False)
                }
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error purchasing number: {e}")
            raise
        except Exception as e:
            logger.error(f"Error purchasing phone number: {e}")
            raise
    
    def configure_voice(
        self,
        phone_sid: str,
        voice_url: str
    ) -> bool:
        """
        Configure phone number for voice calls
        
        Args:
            phone_sid: Twilio SID of the phone number
            voice_url: Webhook URL for incoming calls (LiveKit SIP endpoint)
            
        Returns:
            True if successful
        """
        try:
            self.client.incoming_phone_numbers(phone_sid).update(
                voice_url=voice_url,
                voice_method="POST"
            )
            
            logger.info(f"Configured voice for {phone_sid}: {voice_url}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error configuring voice: {e}")
            raise
        except Exception as e:
            logger.error(f"Error configuring voice: {e}")
            raise
    
    def configure_whatsapp(
        self,
        phone_sid: str,
        webhook_url: str
    ) -> bool:
        """
        Configure phone number for WhatsApp
        
        Args:
            phone_sid: Twilio SID of the phone number
            webhook_url: Webhook URL for incoming WhatsApp messages
            
        Returns:
            True if successful
        """
        try:
            self.client.incoming_phone_numbers(phone_sid).update(
                sms_url=webhook_url,
                sms_method="POST"
            )
            
            logger.info(f"Configured WhatsApp for {phone_sid}: {webhook_url}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error configuring WhatsApp: {e}")
            raise
        except Exception as e:
            logger.error(f"Error configuring WhatsApp: {e}")
            raise
    
    def release_phone_number(self, phone_sid: str) -> bool:
        """
        Release (delete) a phone number
        
        Args:
            phone_sid: Twilio SID of the phone number
            
        Returns:
            True if successful
        """
        try:
            self.client.incoming_phone_numbers(phone_sid).delete()
            logger.info(f"Released phone number: {phone_sid}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error releasing number: {e}")
            raise
        except Exception as e:
            logger.error(f"Error releasing phone number: {e}")
            raise
    
    def get_phone_number_details(self, phone_sid: str) -> Dict:
        """
        Get details of a phone number
        
        Args:
            phone_sid: Twilio SID of the phone number
            
        Returns:
            Phone number details
        """
        try:
            number = self.client.incoming_phone_numbers(phone_sid).fetch()
            
            return {
                "sid": number.sid,
                "phone_number": number.phone_number,
                "friendly_name": number.friendly_name,
                "voice_url": number.voice_url,
                "sms_url": number.sms_url,
                "capabilities": {
                    "voice": number.capabilities.get("voice", False),
                    "sms": number.capabilities.get("SMS", False),
                    "mms": number.capabilities.get("MMS", False)
                },
                "status": number.status
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error fetching number details: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching phone number details: {e}")
            raise
    
    def get_account_balance(self) -> Dict:
        """
        Get Twilio account balance
        
        Returns:
            Account balance information
        """
        try:
            balance = self.client.balance.fetch()
            
            return {
                "balance": float(balance.balance),
                "currency": balance.currency
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error fetching balance: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            raise
