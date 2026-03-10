import os
import requests
import logging

logger = logging.getLogger("anam-service")


from backend.services.integration_service import IntegrationService

class AnamService:
    """Service wrapper for the Anam.ai REST API."""

    def __init__(self, workspace_id: str = None, api_key: str = None):
        self.workspace_id = workspace_id
        self.api_key = api_key or IntegrationService.get_provider_key(
            workspace_id=self.workspace_id,
            provider="anam",
            env_fallback="ANAM_API_KEY"
        )
        self.base_url = "https://api.anam.ai/v1"

        if not self.api_key:
            logger.warning("ANAM_API_KEY not found.")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_personas(self):
        """
        List available Anam.ai personas (avatars).
        Returns a list of persona objects.
        """
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/personas"
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                # Anam API may return list directly or wrapped in { "data": [...] }
                if isinstance(data, list):
                    return data
                return data.get("data", data.get("personas", []))
            else:
                logger.error(f"Failed to list Anam personas: {response.status_code} {response.text}")
                return []
        except Exception as e:
            logger.error(f"Anam API Error (list_personas): {e}")
            return []

    def list_avatars(self):
        """
        List available stock avatars from Anam.ai.
        """
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/avatars"
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                return data.get("data", data.get("avatars", []))
            else:
                logger.error(f"Failed to list Anam avatars: {response.status_code} {response.text}")
                return []
        except Exception as e:
            logger.error(f"Anam API Error (list_avatars): {e}")
            return []

    def get_persona(self, persona_id: str):
        """
        Get details of a specific Anam persona.
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/personas/{persona_id}"
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def create_persona(self, name: str, avatar_id: str, system_prompt: str = "", **kwargs):
        """
        Create a new Anam persona.
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/personas"
            payload = {
                "name": name,
                "avatarId": avatar_id,
                "systemPrompt": system_prompt or "You are a helpful AI assistant.",
            }
            payload.update(kwargs)

            response = requests.post(url, headers=self._get_headers(), json=payload)
            if response.status_code in [200, 201]:
                logger.info(f"Created Anam persona: {response.json()}")
                return response.json()
            else:
                logger.error(f"Failed to create Anam persona: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Anam API Error (create_persona): {e}")
            return None
