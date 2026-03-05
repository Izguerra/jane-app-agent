"""
Supabase Vault Secrets Manager

This module provides secure access to secrets stored in Supabase Vault.
Use this instead of reading sensitive values directly from .env files.
"""

import os
from typing import Optional, Dict
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class VaultSecrets:
    """
    Manages access to secrets stored in Supabase Vault.
    
    Usage:
        secrets = VaultSecrets()
        mistral_key = secrets.get('mistral_api_key')
        
    Or use the singleton:
        from backend.lib.vault_secrets import get_secret
        mistral_key = get_secret('mistral_api_key')
    """
    
    _instance = None
    _cache: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._db = None
    
    def _get_db_session(self):
        """Get a database session for vault queries."""
        if self._db is None:
            from backend.database import SessionLocal
            self._db = SessionLocal()
        return self._db
    
    def get(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Get a secret from Supabase Vault.
        
        Args:
            secret_name: The name of the secret in the vault
            fallback_env_var: Optional environment variable to check if vault fails
            
        Returns:
            The decrypted secret value, or None if not found
        """
        # Check cache first
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            db = self._get_db_session()
            from sqlalchemy import text
            
            result = db.execute(
                text("SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = :name"),
                {"name": secret_name}
            ).fetchone()
            
            if result and result[0]:
                self._cache[secret_name] = result[0]
                return result[0]
                
        except Exception as e:
            logger.warning(f"Failed to fetch secret '{secret_name}' from vault: {e}")
        
        # Fallback to environment variable if provided
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.info(f"Using fallback env var for '{secret_name}'")
                return env_value
        
        return None
    
    def get_required(self, secret_name: str, fallback_env_var: Optional[str] = None) -> str:
        """
        Get a required secret - raises an error if not found.
        
        Args:
            secret_name: The name of the secret in the vault
            fallback_env_var: Optional environment variable to check if vault fails
            
        Returns:
            The decrypted secret value
            
        Raises:
            ValueError: If the secret is not found
        """
        value = self.get(secret_name, fallback_env_var)
        if value is None:
            raise ValueError(f"Required secret '{secret_name}' not found in vault or environment")
        return value
    
    def refresh_cache(self):
        """Clear the secrets cache to force re-fetching from vault."""
        self._cache.clear()
    
    def close(self):
        """Close the database connection."""
        if self._db:
            self._db.close()
            self._db = None


# Singleton instance
_vault = None


def get_vault() -> VaultSecrets:
    """Get the singleton VaultSecrets instance."""
    global _vault
    if _vault is None:
        _vault = VaultSecrets()
    return _vault


def get_secret(secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret from the vault.
    
    Args:
        secret_name: The name of the secret in the vault
        fallback_env_var: Optional environment variable to check if vault fails
        
    Returns:
        The decrypted secret value, or None if not found
    """
    return get_vault().get(secret_name, fallback_env_var)


def get_required_secret(secret_name: str, fallback_env_var: Optional[str] = None) -> str:
    """
    Get a required secret - raises an error if not found.
    
    Args:
        secret_name: The name of the secret in the vault
        fallback_env_var: Optional environment variable to check if vault fails
        
    Returns:
        The decrypted secret value
        
    Raises:
        ValueError: If the secret is not found
    """
    return get_vault().get_required(secret_name, fallback_env_var)


# Secret name constants for type safety
class SecretNames:
    """Constants for vault secret names."""
    MISTRAL_API_KEY = "mistral_api_key"
    STRIPE_SECRET_KEY = "stripe_secret_key"
    STRIPE_WEBHOOK_SECRET = "stripe_webhook_secret"
    TWILIO_ACCOUNT_SID = "twilio_account_sid"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
    LIVEKIT_API_KEY = "livekit_api_key"
    LIVEKIT_API_SECRET = "livekit_api_secret"
    DEEPGRAM_API_KEY = "deepgram_api_key"
    ELEVENLABS_API_KEY = "elevenlabs_api_key"
    PINECONE_API_KEY = "pinecone_api_key"
    GOOGLE_CLIENT_SECRET = "google_client_secret"
    META_APP_SECRET = "meta_app_secret"
    ENCRYPTION_KEY = "encryption_key"
    S3_ACCESS_KEY = "s3_access_key"
    S3_SECRET_KEY = "s3_secret_key"
    RESEND_API_KEY = "resend_api_key"
    OPENROUTER_API_KEY = "openrouter_api_key"
    AUTH_SECRET = "auth_secret"
