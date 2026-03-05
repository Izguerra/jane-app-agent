import os
import logging
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

def get_ai_client(async_mode=True):
    """
    Returns Mistral Direct AI client.
    """
    mistral_key = os.getenv("MISTRAL_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    client_cls = AsyncOpenAI if async_mode else OpenAI
    
    if mistral_key:
        # Mistral Direct
        return client_cls(api_key=mistral_key, base_url="https://api.mistral.ai/v1"), "mistral-small-latest"
        
    if openrouter_key:
        # Mistral via OpenRouter
        return client_cls(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1"), "mistralai/mistral-small-24b-instruct-2501"
        
    raise ValueError("Mistral API Key (MISTRAL_API_KEY) not found in environment.")
