import os
# Must set these before importing oauthlib-related modules
if os.getenv("ENVIRONMENT") != "production":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Relax scope validation to handle cases where Google returns extra scopes
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from backend.database import get_db
from backend.models_db import Integration, Workspace
from backend.auth import get_current_user, AuthUser
from backend.security import encrypt_text
from sqlalchemy.orm import Session
import os
import json
import logging
import requests

logger = logging.getLogger("auth-router")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- GOOGLE CONFIG ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# We use a single callback for all Google services to simplify Console configuration
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

GOOGLE_SCOPES_MAP = {
    "google_calendar": [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    "gmail_mailbox": [
        "https://mail.google.com/",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    "google_drive": [
        "https://www.googleapis.com/auth/drive",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
}

# --- MICROSOFT CONFIG ---
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/auth/outlook/callback")
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"
MICROSOFT_SCOPES = ["offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Calendars.ReadWrite"]


# --- GOOGLE ROUTES ---

async def initiate_google_flow(provider: str):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google credentials not configured")

    scopes = GOOGLE_SCOPES_MAP.get(provider)
    if not scopes:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=scopes,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    # Store provider in state so callback knows which integration to update
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=provider 
    )
    
    return RedirectResponse(authorization_url)

@router.get("/google/login")
async def google_login(request: Request, scope: str = None):
    # Map 'scope' param (from frontend) to internal provider name
    # Default is google_calendar
    provider = "google_calendar"
    if scope == "drive":
        provider = "google_drive"
        
    return await initiate_google_flow(provider)

@router.get("/gmail/login")
async def gmail_login(request: Request):
    return await initiate_google_flow("gmail_mailbox")

@router.get("/google/callback")
async def google_callback(
    request: Request,
    state: str = None, # provider name passed back
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    print(f"DEBUG: RAW CALLBACK HIT. Code={bool(code)}, State={state}, Error={error}")
    if error:
        raise HTTPException(status_code=400, detail=f"Google Auth Error: {error}")
    
    if not code:
         raise HTTPException(status_code=400, detail="Missing auth code")

    # Default to google_calendar if state is missing (legacy support)
    provider_name = state if state in GOOGLE_SCOPES_MAP else "google_calendar"
    
    print(f"DEBUG: Google Callback for provider: {provider_name}")

    try:
        current_user = get_current_user(request, authorization=None, db=db)
    except Exception as e:
        logger.error(f"Auth invalid during callback: {e}")
        # Redirect to login or show error page?
        raise HTTPException(status_code=401, detail=f"User not authenticated: {e}")

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google config missing")

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        # Restore scopes as it is required by from_client_config
        # OAUTHLIB_RELAX_TOKEN_SCOPE env var handles the mismatch
        scopes=GOOGLE_SCOPES_MAP[provider_name], 
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=state
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Failed to fetch Google token: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch token")

    credentials = flow.credentials
    
    # Auto-detect provider from scopes if state is missing or default
    # This handles cases where state is lost during redirect
    granted_scopes = " ".join(credentials.scopes) if credentials.scopes else ""
    if "mail.google.com" in granted_scopes:
        provider_name = "gmail_mailbox"
        logger.info(f"Auto-detected provider from scopes: {provider_name}")
    elif "calendar" in granted_scopes and "mail.google.com" not in granted_scopes:
        provider_name = "google_calendar"
        logger.info(f"Auto-detected provider from scopes: {provider_name}")
    elif "drive" in granted_scopes:
        provider_name = "google_drive"
        logger.info(f"Auto-detected provider from scopes: {provider_name}")
    
    try:
        workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        
        encrypted_creds = encrypt_text(json.dumps(creds_data))
        logger.info(f"Generated encrypted credentials. Length: {len(encrypted_creds) if encrypted_creds else 0}")
        
        # Build default settings based on provider
        default_settings = {}
        if provider_name == "google_calendar":
            default_settings = {"can_view_own_events": True, "can_edit_own_events": True, "can_delete_own_events": True}
        elif provider_name == "gmail_mailbox":
            default_settings = {"can_read_emails": True, "can_send_emails": True, "can_search_emails": True}
        elif provider_name == "google_drive":
            default_settings = {"can_list_files": True, "can_read_files": True, "can_search_files": True, "can_upload_files": True}

        # Update or Create Integration
        integration = db.query(Integration).filter(
            Integration.workspace_id == workspace.id,
            Integration.provider == provider_name
        ).first()

        logger.info(f"Processing callback for {provider_name}. Found existing: {integration is not None}")

        if integration:
            integration.credentials = encrypted_creds
            integration.is_active = True
            logger.info(f"Updating integration {integration.id} to is_active=True")
            
            # Merge defaults into existing settings (handles empty "{}" case)
            current_settings = json.loads(integration.settings) if integration.settings else {}
            for k, v in default_settings.items():
                if k not in current_settings:
                    current_settings[k] = v
            integration.settings = json.dumps(current_settings)
        else:
            from backend.database import generate_integration_id
            integration = Integration(
                id=generate_integration_id(),
                workspace_id=workspace.id,
                provider=provider_name,
                credentials=encrypted_creds,
                settings=json.dumps(default_settings),
                is_active=True
            )
            logger.info(f"Creating new integration {integration.id} with is_active=True")
            db.add(integration)
        
        db.commit()
        db.refresh(integration)
        logger.info(f"Integration {integration.id} saved. Active status: {integration.is_active}")
        
    except Exception as e:
        logger.error(f"Database error saving integration: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database error")
        
    # Redirect back
    import time
    redirect_url = f"http://localhost:3000/{workspace.id}/dashboard/integrations?success=true&cb={int(time.time())}"
    return RedirectResponse(url=redirect_url, status_code=302)


# --- MICROSOFT ROUTES ---

@router.get("/outlook/login")
async def outlook_login(request: Request, scope: str = None):
    # scope param can be 'calendar' or empty (default mail+calendar)
    # We always request full scopes for simplicity as permissions are managed by app 
    # but we could separate if strictly needed. 
    # For now, "Outlook Mail" and "Outlook Calendar" backend integrations
    # will share the same credentials if user connects twice, or we can use distinct providers?
    # To keep it clean: 
    # - If user clicks Outlook Mail -> Integration 'outlook_mailbox'
    # - If user clicks Outlook Calendar -> Integration 'outlook_calendar'
    # We pass this intent in 'state'.
    
    target_provider = "outlook_mailbox"
    if scope == "calendar":
        target_provider = "outlook_calendar"

    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Microsoft credentials not configured")

    # Construct Auth URL manually
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(MICROSOFT_SCOPES),
        "state": target_provider
    }
    
    import urllib.parse
    query_string = urllib.parse.urlencode(params)
    auth_url = f"{MICROSOFT_AUTHORITY}/oauth2/v2.0/authorize?{query_string}"
    
    return RedirectResponse(auth_url)

@router.get("/outlook/callback")
async def outlook_callback(
    request: Request,
    code: str = None,
    state: str = None, # target_provider
    error: str = None,
    db: Session = Depends(get_db)
):
    if error:
        raise HTTPException(status_code=400, detail=f"Outlook Auth Error: {error}")
    
    if not code:
         raise HTTPException(status_code=400, detail="Missing auth code")
         
    target_provider = state if state in ["outlook_mailbox", "outlook_calendar"] else "outlook_mailbox"

    try:
        current_user = get_current_user(request, authorization=None, db=db)
    except:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
         raise HTTPException(status_code=500, detail="Microsoft config missing")
         
    # Exchange code for token
    token_url = f"{MICROSOFT_AUTHORITY}/oauth2/v2.0/token"
    data = {
        "client_id": MICROSOFT_CLIENT_ID,
        "scope": " ".join(MICROSOFT_SCOPES),
        "code": code,
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": MICROSOFT_CLIENT_SECRET
    }
    
    try:
        import requests
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch Microsoft token: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch token")
        
    # Save credential
    try:
        workspace = db.query(Workspace).filter(Workspace.team_id == current_user.team_id).first()
        if not workspace:
             raise HTTPException(status_code=404, detail="Workspace not found")
             
        # Normalize token data
        creds_save = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope")
        }
        
        encrypted_creds = encrypt_text(json.dumps(creds_save))
        
        # Default settings
        default_settings = {}
        if target_provider == "outlook_mailbox":
            default_settings = {"can_read_emails": True, "can_send_emails": True, "can_search_emails": True}
        else:
            default_settings = {"can_view_events": True, "can_create_events": True, "can_edit_events": True}
            
        # Update/Create
        integration = db.query(Integration).filter(
            Integration.workspace_id == workspace.id,
            Integration.provider == target_provider
        ).first()

        if integration:
            integration.credentials = encrypted_creds
            integration.is_active = True
            
            # Merge defaults into existing settings (handles empty "{}" case)
            current_settings = json.loads(integration.settings) if integration.settings else {}
            for k, v in default_settings.items():
                if k not in current_settings:
                    current_settings[k] = v
            integration.settings = json.dumps(current_settings)
        else:
            from backend.database import generate_integration_id
            integration = Integration(
                id=generate_integration_id(),
                workspace_id=workspace.id,
                provider=target_provider,
                credentials=encrypted_creds,
                settings=json.dumps(default_settings),
                is_active=True
            )
            db.add(integration)
            
        # Optional: Since Outlook tokens cover both Mail and Calendar, 
        # we COULD automatically enable the other one too if we wanted, 
        # but user might want them separate. 
        # However, to be nice, we can save the same credentials to the *other* integration 
        # if it doesn't exist, but keep it inactive?
        # Let's keep it simple: one integration per button click.
        
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    import time
    redirect_url = f"http://localhost:3000/{workspace.id}/dashboard/integrations?success=true&cb={int(time.time())}"
    return RedirectResponse(url=redirect_url, status_code=302)

