import os
import logging
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

from backend.services.integration_service import IntegrationService

def get_ai_client(workspace_id: str = None, async_mode=True):
    """
    Returns AI client (Mistral or OpenRouter).
    """
    mistral_key = IntegrationService.get_provider_key(workspace_id, "mistral", "MISTRAL_API_KEY")
    openrouter_key = IntegrationService.get_provider_key(workspace_id, "openrouter", "OPENROUTER_API_KEY")
    
    client_cls = AsyncOpenAI if async_mode else OpenAI
    
    if mistral_key:
        return client_cls(api_key=mistral_key, base_url="https://api.mistral.ai/v1"), "mistral-small-latest"
        
    if openrouter_key:
        return client_cls(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1"), "mistralai/mistral-small-24b-instruct-2501"
        
    raise ValueError("AI API Key not found for workspace or environment.")
