import os
import base64
from cryptography.fernet import Fernet
import logging

class CryptoService:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY")
        if not self.key:
            # Generate a temporary key for development if not provided
            # In production, this should be a tailored error or robust warning
            logging.warning("ENCRYPTION_KEY not found in environment. Generating a temporary key for this session.")
            self.key = Fernet.generate_key().decode()
        
        try:
            self.cipher_suite = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except Exception as e:
            logging.error(f"Failed to initialize CryptoService: {e}")
            raise e

    def encrypt(self, data: str) -> str:
        """Encrypts a string value."""
        if not data:
            return data
        try:
            encrypted_bytes = self.cipher_suite.encrypt(data.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise e

    def decrypt(self, token: str) -> str:
        """Decrypts a token. Returns original string if decryption fails (backward compatibility)."""
        if not token:
            return token
        try:
            decrypted_bytes = self.cipher_suite.decrypt(token.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # Fallback for unencrypted legacy data
            return token
