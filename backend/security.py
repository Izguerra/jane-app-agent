from cryptography.fernet import Fernet
import os
import base64

# In production, this key should be loaded from a secure environment variable
# Generate a key with: Fernet.generate_key()
# For this demo, we'll use a hardcoded key if env var is missing (DO NOT DO THIS IN PROD)
DEFAULT_KEY = Fernet.generate_key()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", DEFAULT_KEY.decode())

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

def encrypt_text(text: str) -> str:
    if not text:
        return ""
    encrypted_text = cipher_suite.encrypt(text.encode())
    return base64.urlsafe_b64encode(encrypted_text).decode()

def decrypt_text(encrypted_text: str) -> str:
    if not encrypted_text:
        return ""
    try:
        decoded_text = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_text = cipher_suite.decrypt(decoded_text)
        return decrypted_text.decode()
    except Exception as e:
        print(f"Decryption failed: {e}")
        return "[Encrypted Data]"
