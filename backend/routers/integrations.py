from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.security import encrypt_text, decrypt_text
import json

router = APIRouter(prefix="/integrations", tags=["integrations"])

class IntegrationConfig(BaseModel):
    provider: str
    credentials: Dict[str, Any]
    settings: Optional[Dict[str, Any]] = {}

class IntegrationResponse(BaseModel):
    id: int
    provider: str
    is_active: bool
    settings: Optional[Dict[str, Any]] = {}

# Mock database
mock_integrations = []

@router.get("", response_model=List[IntegrationResponse])
async def get_integrations():
    # TODO: Fetch from DB
    return mock_integrations

@router.post("/{provider}")
async def configure_integration(provider: str, config: IntegrationConfig):
    global mock_integrations
    
    # Encrypt credentials before saving
    encrypted_creds = encrypt_text(json.dumps(config.credentials))
    
    # Mock save to DB
    # In reality, we'd check if it exists and update, or create new
    new_integration = {
        "id": len(mock_integrations) + 1,
        "provider": provider,
        "is_active": True,
        "settings": config.settings,
        # "credentials": encrypted_creds # Don't return credentials
    }
    
    # Remove existing if any
    mock_integrations = [i for i in mock_integrations if i["provider"] != provider]
    mock_integrations.append(new_integration)
    
    return {"status": "success", "data": new_integration}

@router.delete("/{provider}")
async def remove_integration(provider: str):
    global mock_integrations
    mock_integrations = [i for i in mock_integrations if i["provider"] != provider]
    return {"status": "success"}
