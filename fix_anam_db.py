import os
import json
import uuid
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.models_db import Integration
from backend.services.crypto_service import CryptoService

db = SessionLocal()
crypto = CryptoService()
api_key = os.getenv('ANAM_API_KEY') or 'NTJmMDkyMDQtYjI4ZC00YzM4LTkyYTctN2ZiYjJjM2E2YTI4OjgzR1JpRC96SXpsY3ZEUDQvREsyQzU0Rm1WUElvTzR2bEVPVCtrSDU1emM9'
workspace_id = 'wrk_000V7dMzXJLzP5mYgdf7FzjA3J'

creds_dict = {"ANAM_API_KEY": api_key, "api_key": api_key}
creds_json = json.dumps(creds_dict)
encrypted_creds = crypto.encrypt(creds_json)

existing = db.query(Integration).filter_by(workspace_id=workspace_id, provider='anam').first()
if not existing:
    db.add(Integration(
        id=f"int_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id, 
        provider='anam', 
        credentials=encrypted_creds, 
        is_active=True
    ))
else:
    existing.credentials = encrypted_creds
    existing.is_active = True

db.commit()
db.close()
print('Added/Updated Anam integration for workspace with encryption.')
