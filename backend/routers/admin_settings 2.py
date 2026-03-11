"""
Admin Settings Router
Handles platform settings, security, API keys, and integration toggles
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import secrets
import os
import httpx
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])

# ============================================================================
# Pydantic Models
# ============================================================================

class GeneralSettings(BaseModel):
    company_name: str
    support_email: str
    default_language: str
    timezone: str

class SecurityOverview(BaseModel):
    two_factor_enabled: bool
    password_last_changed: Optional[datetime]
    active_sessions_count: int

class APIKey(BaseModel):
    id: str
    name: str
    key_prefix: str
    last_used_at: Optional[datetime]
    created_at: datetime

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Full key only returned once on creation
    key_prefix: str

class ActiveSession(BaseModel):
    id: str
    device_name: str
    location: str
    ip_address: str
    last_active_at: datetime
    created_at: datetime

class PlatformIntegration(BaseModel):
    id: str
    provider: str
    display_name: str
    description: Optional[str]
    is_enabled: bool
    customer_count: int = 0
    health_status: str = "unknown"  # "operational", "degraded", "down", "unknown"
    last_checked: Optional[datetime] = None

class IntegrationToggle(BaseModel):
    is_enabled: bool

class HealthCheckResponse(BaseModel):
    provider: str
    status: str  # "operational", "degraded", "down"
    message: str
    checked_at: datetime

# ============================================================================
# General Settings Endpoints
# ============================================================================

@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get general platform settings"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = db.execute(text("SELECT * FROM admin_settings LIMIT 1")).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return GeneralSettings(
        company_name=result[1],
        support_email=result[2],
        default_language=result[3],
        timezone=result[4]
    )

@router.put("/general", response_model=GeneralSettings)
async def update_general_settings(
    settings: GeneralSettings,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update general platform settings"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("""
        UPDATE admin_settings 
        SET company_name = ?, support_email = ?, default_language = ?, timezone = ?
    """), (settings.company_name, settings.support_email, settings.default_language, settings.timezone))
    db.commit()
    
    return settings

# ============================================================================
# Security Endpoints
# ============================================================================

@router.get("/security", response_model=SecurityOverview)
async def get_security_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security overview"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db.execute(text("SELECT two_factor_enabled FROM admin_settings LIMIT 1")).fetchone()
    sessions_count = db.execute(text("SELECT COUNT(*) FROM active_sessions")).fetchone()[0]
    
    return SecurityOverview(
        two_factor_enabled=settings[0] if settings else False,
        password_last_changed=None,  # TODO: Track password changes
        active_sessions_count=sessions_count
    )

@router.get("/security/sessions", response_model=List[ActiveSession])
async def get_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of active sessions"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.execute(text("""
        SELECT id, device_name, location, ip_address, last_active_at, created_at
        FROM active_sessions
        ORDER BY last_active_at DESC
    """)).fetchall()
    
    return [
        ActiveSession(
            id=str(row[0]),
            device_name=row[1],
            location=row[2],
            ip_address=row[3],
            last_active_at=row[4],
            created_at=row[5]
        )
        for row in results
    ]

@router.delete("/security/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an active session"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("DELETE FROM active_sessions WHERE id = :id"), {"id": session_id})
    db.commit()
    return {"message": "Session revoked successfully"}

# ============================================================================
# API Keys Endpoints
# ============================================================================

@router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of API keys"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.execute(text("""
        SELECT id, name, key_prefix, last_used_at, created_at
        FROM api_keys
        ORDER BY created_at DESC
    """)).fetchall()
    
    return [
        APIKey(
            id=str(row[0]),
            name=row[1],
            key_prefix=row[2],
            last_used_at=row[3],
            created_at=row[4]
        )
        for row in results
    ]

@router.post("/api-keys", response_model=APIKeyResponse)
async def generate_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key"""
    import uuid
    
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Generate a secure random API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    key_prefix = api_key[:12] + "..."
    
    # Hash the key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Store in database
    key_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO api_keys (id, name, key_hash, key_prefix, created_at)
        VALUES (:id, :name, :key_hash, :key_prefix, :created_at)
    """), {"id": key_id, "name": key_data.name, "key_hash": key_hash, "key_prefix": key_prefix, "created_at": datetime.now()})
    db.commit()
    
    return APIKeyResponse(
        id=key_id,
        name=key_data.name,
        key=api_key,  # Only returned once
        key_prefix=key_prefix
    )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": key_id})
    db.commit()
    return {"message": "API key deleted successfully"}

# ============================================================================
# Platform Integrations Endpoints
# ============================================================================

@router.get("/integrations", response_model=List[PlatformIntegration])
async def get_platform_integrations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of platform integrations with usage stats"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get platform integrations with customer counts
    results = db.execute(text("""
        SELECT 
            pi.id, 
            pi.provider, 
            pi.display_name, 
            pi.description, 
            pi.is_enabled,
            COUNT(DISTINCT i.workspace_id) as customer_count
        FROM platform_integrations pi
        LEFT JOIN integrations i ON pi.provider = i.provider AND i.is_active = true
        GROUP BY pi.id, pi.provider, pi.display_name, pi.description, pi.is_enabled
        ORDER BY pi.display_name
    """)).fetchall()
    
    integrations = []
    for row in results:
        # Determine strict health status based on configuration presence
        provider = row[1]
        is_enabled = row[4]
        health_status = "unknown"
        
        if is_enabled:
            # Check for required environment variables
            if provider == "sendgrid":
                health_status = "operational" if os.getenv("SENDGRID_API_KEY") else "down"
            elif provider == "stripe":
                health_status = "operational" if os.getenv("STRIPE_SECRET_KEY") else "down"
            elif provider == "twilio":
                health_status = "operational" if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") else "down"
            else:
                # For providers without global config (WhatsApp, Google Calendar, etc.), assume operational if enabled
                health_status = "operational"
        
        integrations.append(PlatformIntegration(
            id=str(row[0]),
            provider=provider,
            display_name=row[2],
            description=row[3],
            is_enabled=is_enabled,
            customer_count=row[5] or 0,
            health_status=health_status,
            last_checked=datetime.now()
        ))
    
    return integrations

@router.put("/integrations/{provider}", response_model=PlatformIntegration)
async def toggle_integration(
    provider: str,
    toggle: IntegrationToggle,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle platform integration on/off"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update integration status
    db.execute(text("""
        UPDATE platform_integrations 
        SET is_enabled = :is_enabled
        WHERE provider = :provider
    """), {"is_enabled": toggle.is_enabled, "provider": provider})
    db.commit()
    
    # Get updated integration
    result = db.execute(text("""
        SELECT id, provider, display_name, description, is_enabled
        FROM platform_integrations
        WHERE provider = :provider
    """), {"provider": provider}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Get customer count
    customer_count = db.execute(text("""
        SELECT COUNT(DISTINCT workspace_id)
        FROM integrations
        WHERE provider = :provider AND is_active = true
    """), {"provider": provider}).fetchone()[0]
    
    return PlatformIntegration(
        id=str(result[0]),
        provider=result[1],
        display_name=result[2],
        description=result[3],
        is_enabled=result[4],
        customer_count=customer_count or 0,
        health_status="operational" if result[4] else "unknown",
        last_checked=datetime.now()
    )

@router.post("/integrations/{provider}/test", response_model=HealthCheckResponse)
async def test_integration_connection(
    provider: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection to integration API"""
    # Verify admin role
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Test connection based on provider
    if provider == "stripe":
        api_key = os.getenv("STRIPE_SECRET_KEY")
        if not api_key:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message="Stripe API key not configured in environment variables",
                checked_at=datetime.now()
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.stripe.com/v1/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return HealthCheckResponse(
                        provider=provider,
                        status="operational",
                        message="Stripe API connection successful",
                        checked_at=datetime.now()
                    )
                else:
                    return HealthCheckResponse(
                        provider=provider,
                        status="degraded",
                        message=f"Stripe API returned status {response.status_code}",
                        checked_at=datetime.now()
                    )
        except Exception as e:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message=f"Failed to connect to Stripe API: {str(e)}",
                checked_at=datetime.now()
            )
    
    elif provider == "sendgrid":
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message="SendGrid API key not configured in environment variables",
                checked_at=datetime.now()
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.sendgrid.com/v3/scopes",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return HealthCheckResponse(
                        provider=provider,
                        status="operational",
                        message="SendGrid API connection successful",
                        checked_at=datetime.now()
                    )
                else:
                    return HealthCheckResponse(
                        provider=provider,
                        status="degraded",
                        message=f"SendGrid API returned status {response.status_code}",
                        checked_at=datetime.now()
                    )
        except Exception as e:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message=f"Failed to connect to SendGrid API: {str(e)}",
                checked_at=datetime.now()
            )

    elif provider == "twilio":
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not sid or not token:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message="Twilio credentials (SID/Token) not configured in environment variables",
                checked_at=datetime.now()
            )
            
        try:
            async with httpx.AsyncClient() as client:
                # Basic Auth is SID:Token
                response = await client.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json",
                    auth=(sid, token),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    friendly_name = data.get("friendly_name")
                    return HealthCheckResponse(
                        provider=provider,
                        status="operational",
                        message=f"Twilio API connected. Account: {friendly_name} ({status})",
                        checked_at=datetime.now()
                    )
                else:
                    return HealthCheckResponse(
                        provider=provider,
                        status="degraded",
                        message=f"Twilio API returned status {response.status_code}",
                        checked_at=datetime.now()
                    )
        except Exception as e:
            return HealthCheckResponse(
                provider=provider,
                status="down",
                message=f"Failed to connect to Twilio API: {str(e)}",
                checked_at=datetime.now()
            )
    
    elif provider == "whatsapp":
        # WhatsApp uses customer-specific phone numbers and tokens
        return HealthCheckResponse(
            provider=provider,
            status="operational",
            message="WhatsApp uses customer-specific phone numbers and tokens (no platform-wide key needed)",
            checked_at=datetime.now()
        )
    
    elif provider == "google_calendar":
        # Google Calendar uses OAuth2 per-user authentication
        return HealthCheckResponse(
            provider=provider,
            status="operational",
            message="Google Calendar uses OAuth2 per-user authentication (no platform-wide key needed)",
            checked_at=datetime.now()
        )

    elif provider in ["gmail_mailbox", "outlook_mailbox", "icloud_mailbox", "exchange", "google_mail"]:
        # User-level email integrations
        return HealthCheckResponse(
            provider=provider,
            status="operational",
            message=f"{provider.replace('_', ' ').title()} uses per-user credential management",
            checked_at=datetime.now()
        )
    
    else:
        return HealthCheckResponse(
            provider=provider,
            status="unknown",
            message="Health check not implemented for this provider",
            checked_at=datetime.now()
        )
