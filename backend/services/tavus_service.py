import os
import requests
import logging

logger = logging.getLogger("tavus-service")

class TavusService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVUS_API_KEY")
        self.base_url = "https://tavusapi.com/v2" 
        
        if not self.api_key:
            logger.warning("Tavus API Key is missing.")

    def _get_headers(self):
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def list_replicas(self):
        """
        List available replicas (avatars).
        """
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/replicas" 
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                # API v2 returns { "data": [...] }
                return data.get("data", [])
            else:
                logger.error(f"Failed to list replicas: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Tavus API Error: {e}")
            return []

    def list_personas(self):
        """
        List available personas.
        """
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/personas" 
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                logger.error(f"Failed to list personas: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Tavus API Error (list_personas): {e}")
            return []

    def get_replica(self, replica_id: str):
        """
        Get details of a specific replica.
        """
        if not self.api_key: return None
        
        try:
            url = f"{self.base_url}/replicas/{replica_id}"
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except: return None

    def get_persona(self, persona_id: str):
        """
        Get details of a specific persona.
        """
        if not self.api_key: return None
        
        try:
            url = f"{self.base_url}/personas/{persona_id}"
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except: return None

    def create_conversation(self, replica_id: str, persona_id: str = None, name: str = "New Conversation"):
        """
        Creates a new conversation in Tavus.
        NOTE: This is typically handled by the LiveKit Plugin (avatar_agent.py), 
        but provided here for direct API usage if needed.
        """
        if not self.api_key: return None
        
        try:
            url = f"{self.base_url}/conversations"
            
            payload = {
                "replica_id": replica_id,
                "conversation_name": name
            }
            if persona_id:
                payload["persona_id"] = persona_id
            
            # Note: properties like livekit_url are not standard v2 properties according to public docs,
            # but might be supported for specific external integrations. 
            # We omit them here to prioritize doc compliance unless forced.
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            if response.status_code in [200, 201]:
                logger.info(f"Tavus conversation started: {response.json().get('conversation_id')}")
                return response.json()
            else:
                logger.error(f"Failed to start Tavus conversation: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Tavus API Error (create_conversation): {e}")
            return None
