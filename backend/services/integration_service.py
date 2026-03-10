import os
import json
import logging
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models_db import Integration
from backend.services.crypto_service import CryptoService

logger = logging.getLogger(__name__)

class IntegrationService:
    """
    Service for securely fetching integration credentials and API keys.
    Prioritizes database configuration per-workspace, falling back to environment variables.
    """

    @staticmethod
    def get_provider_key(workspace_id: str, provider: str, env_fallback: str) -> str:
        """
        Fetches the API key for a specific provider.
        1. Checks the `integrations` table for the workspace and provider.
        2. Parses the `credentials` JSON to find the API key.
        3. Falls back to the environment variable if not found or disabled.
        
        Args:
            workspace_id (str): The workspace to fetch keys for.
            provider (str): The provider name (e.g. 'openweathermap', 'openai').
            env_fallback (str): The name of the environment variable (e.g. 'OPENWEATHERMAP_API_KEY').
            
        Returns:
            str: The API key.
        """
        db: Session = SessionLocal()
        try:
            # 1. Check DB first
            integration = db.query(Integration).filter(
                Integration.workspace_id == workspace_id,
                Integration.provider == provider,
                Integration.is_active == True
            ).first()

            if integration and integration.credentials:
                try:
                    # Decrypt the credentials string before parsing
                    crypto = CryptoService()
                    decrypted_creds = crypto.decrypt(integration.credentials)
                    
                    # Parse the JSON credentials string
                    creds = json.loads(decrypted_creds)
                    
                    # 1. First check for exact env_fallback match (e.g. TWILIO_ACCOUNT_SID)
                    if env_fallback in creds and creds[env_fallback]:
                        logger.debug(f"Found exact match {env_fallback} for {provider} in database")
                        return creds[env_fallback]
                        
                    # 2. Check case-insensitive match
                    for k, v in creds.items():
                        if k.upper() == env_fallback.upper() and v:
                            return v
                            
                    # 3. Look for common generic key names in the credentials JSON
                    key_variants = ["api_key", "apiKey", "key", "token", "secret", "secret_key"]
                    
                    for variant in key_variants:
                        if variant in creds and creds[variant]:
                            logger.debug(f"Found {provider} API key via variant {variant} in database")
                            return creds[variant]
                            
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse credentials JSON for provider {provider} in workspace {workspace_id}")

            # 2. Fall back to environment variable

            logger.debug(f"Falling back to environment variable {env_fallback} for provider {provider}")
            env_val = os.getenv(env_fallback)
            
            if env_val:
                 return env_val
                 
            return ""

        except Exception as e:
            logger.error(f"Error fetching provider key for {provider}: {e}")
            # Ensure we still try env variable on DB failure
            return os.getenv(env_fallback, "")
        finally:
            db.close()
    @staticmethod
    async def async_get_provider_key(workspace_id: str, provider: str, env_fallback: str) -> str:
        """Async version of get_provider_key to avoid blocking the event loop."""
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        # Wrap the synchronous call in a partial to pass arguments
        func = partial(IntegrationService.get_provider_key, workspace_id, provider, env_fallback)
        return await loop.run_in_executor(None, func)
