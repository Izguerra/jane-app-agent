import sys
import os
import json
import logging

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models_db import Integration
from backend.security import encrypt_text, decrypt_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("encrypt_integrations")

def main():
    db = SessionLocal()
    try:
        integrations = db.query(Integration).filter(Integration.credentials.isnot(None)).all()
        logger.info(f"Found {len(integrations)} integrations with credentials.")
        
        updated_count = 0
        
        for integration in integrations:
            creds_str = integration.credentials
            if not creds_str:
                continue
                
            # Check if it's already encrypted
            is_encrypted = False
            try:
                # If decrypt_text works, it's likely encrypted (or a valid base64 fernet token)
                # Note: decrypt_text returns "[Encrypted Data]" on failure, or throws?
                # Let's inspect security.py again to be sure. 
                # Just assuming standard behavior: if it's plaintext JSON, decrypt might fail or return garbage.
                # A better check: try to parse as JSON directly. If it parses, it's plaintext.
                json.loads(creds_str)
                is_plaintext = True
            except json.JSONDecodeError:
                is_plaintext = False
            except Exception:
                # If unforeseen error, assume not simple plaintext JSON
                is_plaintext = False
                
            if is_plaintext:
                logger.info(f"Encrypting credentials for integration {integration.id} ({integration.provider})...")
                encrypted = encrypt_text(creds_str)
                integration.credentials = encrypted
                updated_count += 1
            else:
                # Double check if it CAN be decrypted
                decrypted = decrypt_text(creds_str)
                if decrypted == "[Encrypted Data]" or not decrypted:
                     # This implies it failed to decrypt OR was garbage. 
                     # However, if we ruled out plaintext JSON above, and it fails to decrypt, 
                     # it might be corrupted, or just already encrypted with a different key?
                     # For safety, if it looks like noise but isn't JSON, we assume it's encrypted.
                     pass
        
        if updated_count > 0:
            db.commit()
            logger.info(f"Successfully encrypted {updated_count} integration credentials.")
        else:
            logger.info("No plaintext credentials found requiring encryption.")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
