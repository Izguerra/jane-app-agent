"""
Meta WhatsApp Business API Service

Handles:
- Sending WhatsApp messages
- Sending template messages
- Managing message templates
- Webhook signature verification
"""

import os
import logging
import hmac
import hashlib
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MetaWhatsAppService:
    """Service for Meta WhatsApp Business API"""
    
    BASE_URL = "https://graph.facebook.com/v24.0"
    
    def __init__(self, access_token: str, phone_number_id: str):
        """
        Initialize Meta WhatsApp service
        
        Args:
            access_token: Meta system user access token
            phone_number_id: WhatsApp phone number ID
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        logger.info(f"Meta WhatsApp service initialized for phone number ID: {phone_number_id}")
    
    def send_message(self, to: str, message: str) -> Dict:
        """
        Send text message
        
        Args:
            to: Recipient phone number (E.164 format)
            message: Message text
            
        Returns:
            API response with message ID
        """
        try:
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
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent WhatsApp message to {to}: {result.get('messages', [{}])[0].get('id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise
    
    def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send template message (required for outbound messages outside 24h window)
        
        Args:
            to: Recipient phone number (E.164 format)
            template_name: Name of approved template
            language_code: Template language code
            components: Template components (parameters, buttons, etc.)
            
        Returns:
            API response with message ID
        """
        try:
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
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent WhatsApp template '{template_name}' to {to}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp template: {e}")
            raise
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark message as read
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            True if successful
        """
        try:
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
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            logger.debug(f"Marked message {message_id} as read")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    def create_template(
        self,
        waba_id: str,
        name: str,
        category: str,
        language: str,
        components: List[Dict]
    ) -> Dict:
        """
        Create a new message template
        
        Args:
            waba_id: WhatsApp Business Account ID
            name: Template name (lowercase, underscores only)
            category: MARKETING, UTILITY, or AUTHENTICATION
            language: Language code (e.g., 'en', 'es')
            components: Template components (header, body, footer, buttons)
            
        Returns:
            Template creation response with template ID
        """
        try:
            url = f"{self.BASE_URL}/{waba_id}/message_templates"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "name": name,
                "category": category,
                "language": language,
                "components": components
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created WhatsApp template '{name}': {result.get('id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating WhatsApp template: {e}")
            raise
    
    def get_templates(self, waba_id: str) -> List[Dict]:
        """
        Get all message templates for a WhatsApp Business Account
        
        Args:
            waba_id: WhatsApp Business Account ID
            
        Returns:
            List of templates
        """
        try:
            url = f"{self.BASE_URL}/{waba_id}/message_templates"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            templates = result.get("data", [])
            logger.info(f"Retrieved {len(templates)} templates for WABA {waba_id}")
            return templates
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching WhatsApp templates: {e}")
            raise
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
        """
        Verify webhook signature from Meta
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            app_secret: Meta app secret
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Signature format: "sha256=<hash>"
            is_valid = hmac.compare_digest(
                f"sha256={expected_signature}",
                signature
            )
            
            if not is_valid:
                logger.warning("Invalid webhook signature")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
