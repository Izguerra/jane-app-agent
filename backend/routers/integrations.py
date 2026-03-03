from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.services.crypto_service import CryptoService
from backend.database import get_db
from backend.models_db import Integration, Workspace
from backend.auth import get_current_user, AuthUser
from sqlalchemy.orm import Session
import json

from backend.services.tavus_service import TavusService

# Initialize Crypto Service
crypto_service = CryptoService()

router = APIRouter(prefix="/integrations", tags=["integrations"])

class IntegrationConfig(BaseModel):
    provider: str
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = {}

class IntegrationResponse(BaseModel):
    id: str
    provider: str
    is_active: bool
    settings: Optional[Dict[str, Any]] = {}

@router.get("", response_model=List[IntegrationResponse])
async def get_integrations(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        return []
        
    integrations = db.query(Integration).filter(Integration.workspace_id == workspace.id).all()
    
    return [
        IntegrationResponse(
            id=i.id,
            provider=i.provider,
            is_active=i.is_active,
            settings=json.loads(i.settings) if i.settings else {}
        ) for i in integrations
    ]

@router.get("/tavus/replicas")
async def get_tavus_replicas(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if Tavus is enabled
    integration = db.query(Integration).filter(
        Integration.workspace_id == workspace.id,
        Integration.provider == "tavus",
        Integration.is_active == True
    ).first()
    
    if not integration:
        return []
        
    try:
        # Platform Managed Key (Tavus)
        import os
        api_key = os.getenv("TAVUS_API_KEY")
        if not api_key:
             print("TAVUS_API_KEY not found in environment.")
             return []
        
        service = TavusService(api_key=api_key)
        # Pass a flag to verify if integration record is actually active before returning?
        # The query above already filters by active.
        
        replicas = service.list_replicas()
        
        # Transform for UI safely
        return replicas
    except Exception as e:
        print(f"Error fetching replicas: {e}")
        return []

@router.get("/tavus/personas")
async def get_tavus_personas(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    integration = db.query(Integration).filter(
        Integration.workspace_id == workspace.id,
        Integration.provider == "tavus",
        Integration.is_active == True
    ).first()
    
    if not integration:
        return []
        
    try:
        import os
        api_key = os.getenv("TAVUS_API_KEY")
        if not api_key:
             return []
        
        service = TavusService(api_key=api_key)
        personas = service.list_personas()
        return personas
    except Exception as e:
        print(f"Error fetching personas: {e}")
        return []

@router.post("/{provider}")
async def configure_integration(
    provider: str, 
    config: IntegrationConfig,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
         raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if exists
    integration = db.query(Integration).filter(
        Integration.workspace_id == workspace.id,
        Integration.provider == provider
    ).first()
    
    # Validate WhatsApp credentials if applicable
    if provider == "whatsapp" and config.credentials:
        sid = config.credentials.get("account_sid")
        token = config.credentials.get("auth_token")
        
        if sid and token:
            try:
                from twilio.rest import Client
                from twilio.base.exceptions import TwilioRestException
                
                client = Client(sid, token)
                # Try to fetch account details to verify credentials
                client.api.accounts(sid).fetch()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Twilio credentials: {str(e)}")

    # Validate Shopify credentials if applicable
    if provider == "shopify" and config.credentials and config.settings:
        token = config.credentials.get("access_token")
        shop_url = config.settings.get("shop_url")
        
        if token and shop_url:
            try:
                import requests
                # Clean up shop URL
                shop_domain = shop_url.replace("https://", "").replace("http://", "").rstrip("/")
                if not shop_domain.endswith("myshopify.com"):
                     raise ValueError("Shop URL must be a .myshopify.com domain")
                
                # Try to fetch shop info
                response = requests.get(
                    f"https://{shop_domain}/admin/api/2023-10/shop.json",
                    headers={"X-Shopify-Access-Token": token},
                    timeout=5
                )
                
                if response.status_code == 401:
                    raise ValueError("Invalid Access Token")
                elif response.status_code != 200:
                    raise ValueError(f"Failed to connect to Shopify: {response.text}")
                    
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Shopify credentials: {str(e)}")

    # Validate Meta WhatsApp credentials
    if provider == "meta_whatsapp" and config.settings:
        phone_id = config.settings.get("phone_number_id")
        access_token = config.settings.get("access_token")
        
        if phone_id and access_token:
            try:
                import requests
                # Verify token and phone ID by fetching phone number details
                url = f"https://graph.facebook.com/v24.0/{phone_id}"
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code != 200:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                    raise ValueError(f"Meta API validation failed: {error_msg}")
                    
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Meta credentials: {str(e)}")
    
    # SPECIAL HANDLING: Instagram
    # Ensure instagram_account_id is available in settings (unencrypted) for webhook lookup
    if provider == "instagram" and config.credentials and "instagram_account_id" in config.credentials:
        if "instagram_account_id" not in config.settings:
            config.settings["instagram_account_id"] = config.credentials["instagram_account_id"]

    # SPECIAL HANDLING: OpenClaw
    # Verify instances config
    if provider == "openclaw" and config.settings:
        instances = config.settings.get("instances", [])
        # In the future, we can call WorkerConnectionService.validate_instances(instances) here
        # For now, we allow the save.
        pass
            
    # Apply default permissions for manual integrations to prevent empty settings
    default_permissions = {}
    if provider == "icloud_mailbox":
        default_permissions = {"can_read_emails": True, "can_send_emails": True, "can_search_emails": True}
    elif provider == "icloud_calendar":
        default_permissions = {"can_view_own_events": True, "can_edit_own_events": True, "can_delete_own_events": True}
    elif provider == "exchange":
        default_permissions = {"can_read_emails": True, "can_send_emails": True, "can_view_events": True, "can_create_events": True}
        
    if default_permissions:
        if not config.settings:
            config.settings = {}
        for k, v in default_permissions.items():
            if k not in config.settings:
                config.settings[k] = v

    if integration:
        if config.credentials:
            integration.credentials = crypto_service.encrypt(json.dumps(config.credentials))
        integration.settings = json.dumps(config.settings)
        integration.is_active = True
    else:
        # OAuth-based integrations don't require upfront credentials in the config payload
        oauth_providers = ["google_calendar", "exchange", "gmail_mailbox", "outlook_mailbox", "icloud_mailbox", "outlook_calendar", "icloud_calendar", "google_drive"]
        if not config.credentials and provider not in oauth_providers:
             # Tavus Exception: Platform Managed
             # Tavus Exception: Platform Managed
             if provider == "tavus":
                 import os
                 if not os.getenv("TAVUS_API_KEY"):
                     raise HTTPException(status_code=400, detail="System Error: Tavus is not configured on this server.")
             elif provider == "openclaw":
                 # OpenClaw uses settings for instances/connection info
                 pass
             else:
                 print(f"DEBUG: Missing credentials for {provider}")
                 raise HTTPException(status_code=400, detail="Credentials required for new integration")
             
        print(f"DEBUG: Creating new integration for {provider}")
        from backend.database import generate_integration_id
        integration = Integration(
            id=generate_integration_id(),
            workspace_id=workspace.id,
            provider=provider,
            credentials=crypto_service.encrypt(json.dumps(config.credentials)) if config.credentials else None,
            settings=json.dumps(config.settings),
            is_active=True
        )
        db.add(integration)
    
    db.commit()
    db.refresh(integration)
    
    return {
        "status": "success", 
        "data": {
            "id": integration.id,
            "provider": integration.provider,
            "is_active": integration.is_active,
            "settings": config.settings
        }
    }

class VerifyRequest(BaseModel):
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

@router.post("/{provider}/verify")
async def verify_integration(
    provider: str,
    request: VerifyRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify credentials or connection settings for an integration before saving.
    """
    if provider == "openclaw":
        from backend.services.worker_connection_service import WorkerConnectionService
        
        # We expect 'url' and 'api_key' in credentials (for BYO) 
        # OR in settings (if user is just passing them through)
        # The frontend likely sends them as part of the check.
        
        url = None
        api_key = None
        
        # Check credentials first
        if request.credentials:
            url = request.credentials.get("url")
            api_key = request.credentials.get("api_key")
            
        # Fallback to settings
        if not url and request.settings:
            # If verifying a specific instance in the list
            # For now, let's assume the frontend sends single instance details for verification
            url = request.settings.get("url")
            api_key = request.settings.get("api_key")
            
        if not url:
             raise HTTPException(status_code=400, detail="Missing 'url' for verification")
             
        service = WorkerConnectionService(db)
        result = await service.validate_openclaw_connection(url, api_key or "")
        
        if not result.get("valid"):
            raise HTTPException(status_code=400, detail=result.get("error", "Connection failed"))
            
        return {"status": "success", "data": result}
        
    return {"status": "success", "message": "Verification not implemented for this provider"}

@router.delete("/{provider}")
async def remove_integration(
    provider: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
    if not workspace:
         raise HTTPException(status_code=404, detail="Workspace not found")
         
    integration = db.query(Integration).filter(
        Integration.workspace_id == workspace.id,
        Integration.provider == provider
    ).first()
    
    if integration:
        integration.is_active = False
        db.commit()
        
    return {"status": "success"}
