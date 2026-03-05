import os
import requests
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class InstagramService:
    """Service for interacting with Instagram Graph API."""
    
    GRAPH_API_VERSION = "v18.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
    
    @staticmethod
    def send_message(access_token: str, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """
        Send a text message to an Instagram user.
        
        Args:
            access_token: Page Access Token
            recipient_id: Instagram Scoped User ID (IGSID) of the recipient
            message_text: Text to send
            
        Returns:
            JSON response from Graph API
        """
        url = f"{InstagramService.BASE_URL}/me/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "access_token": access_token
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Instagram message: {e}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    @staticmethod
    def verify_token(token: str) -> bool:
        """
        Verify if a token is valid (basic check).
        In a real app, you might call /debug_token endpoint.
        """
        return bool(token)
