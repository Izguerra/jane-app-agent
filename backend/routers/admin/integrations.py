import os
import httpx
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.auth import get_current_user, AuthUser
from backend.database import get_db
from .models import PlatformIntegration, IntegrationToggle, HealthCheckResponse

router = APIRouter(tags=["Admin - Platform Integrations"])

@router.get("/integrations", response_model=List[PlatformIntegration])
async def get_platform_integrations(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of platform integrations with usage stats."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.execute(text("""
        SELECT pi.id, pi.provider, pi.display_name, pi.description, pi.is_enabled,
               COUNT(DISTINCT i.workspace_id) as customer_count
        FROM platform_integrations pi
        LEFT JOIN integrations i ON pi.provider = i.provider AND i.is_active = true
        GROUP BY pi.id, pi.provider, pi.display_name, pi.description, pi.is_enabled
        ORDER BY pi.display_name
    """)).fetchall()
    
    integrations = []
    for row in results:
        provider, is_enabled = row[1], row[4]
        health_status = "unknown"
        if is_enabled:
            if provider == "sendgrid": health_status = "operational" if os.getenv("SENDGRID_API_KEY") else "down"
            elif provider == "stripe": health_status = "operational" if os.getenv("STRIPE_SECRET_KEY") else "down"
            elif provider == "twilio": health_status = "operational" if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") else "down"
            else: health_status = "operational"
        
        integrations.append(PlatformIntegration(
            id=str(row[0]), provider=provider, display_name=row[2], description=row[3],
            is_enabled=is_enabled, customer_count=row[5] or 0, health_status=health_status,
            last_checked=datetime.now()
        ))
    return integrations

@router.put("/integrations/{provider}", response_model=PlatformIntegration)
async def toggle_integration(
    provider: str,
    toggle: IntegrationToggle,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle platform integration on/off."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("UPDATE platform_integrations SET is_enabled = :e WHERE provider = :p"), {"e": toggle.is_enabled, "p": provider})
    db.commit()
    
    res = db.execute(text("SELECT id, provider, display_name, description, is_enabled FROM platform_integrations WHERE provider = :p"), {"p": provider}).fetchone()
    if not res: raise HTTPException(status_code=404, detail="Integration not found")
    
    count = db.execute(text("SELECT COUNT(DISTINCT workspace_id) FROM integrations WHERE provider = :p AND is_active = true"), {"p": provider}).fetchone()[0]
    
    return PlatformIntegration(
        id=str(res[0]), provider=res[1], display_name=res[2], description=res[3],
        is_enabled=res[4], customer_count=count or 0, health_status="operational" if res[4] else "unknown",
        last_checked=datetime.now()
    )

@router.post("/integrations/{provider}/test", response_model=HealthCheckResponse)
async def test_integration_connection(
    provider: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection to integration API."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if provider == "stripe":
        key = os.getenv("STRIPE_SECRET_KEY")
        if not key: return HealthCheckResponse(provider=provider, status="down", message="No API key", checked_at=datetime.now())
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.stripe.com/v1/balance", headers={"Authorization": f"Bearer {key}"}, timeout=10.0)
                return HealthCheckResponse(provider=provider, status="operational" if resp.status_code == 200 else "degraded", message="Success" if resp.status_code == 200 else f"Status {resp.status_code}", checked_at=datetime.now())
        except Exception as e: return HealthCheckResponse(provider=provider, status="down", message=str(e), checked_at=datetime.now())
    
    elif provider == "sendgrid":
        key = os.getenv("SENDGRID_API_KEY")
        if not key: return HealthCheckResponse(provider=provider, status="down", message="No API key", checked_at=datetime.now())
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.sendgrid.com/v3/scopes", headers={"Authorization": f"Bearer {key}"}, timeout=10.0)
                return HealthCheckResponse(provider=provider, status="operational" if resp.status_code == 200 else "degraded", message="Success" if resp.status_code == 200 else f"Status {resp.status_code}", checked_at=datetime.now())
        except Exception as e: return HealthCheckResponse(provider=provider, status="down", message=str(e), checked_at=datetime.now())

    elif provider == "twilio":
        sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
        if not sid or not token: return HealthCheckResponse(provider=provider, status="down", message="No credentials", checked_at=datetime.now())
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json", auth=(sid, token), timeout=10.0)
                if resp.status_code == 200: return HealthCheckResponse(provider=provider, status="operational", message="Connected", checked_at=datetime.now())
                return HealthCheckResponse(provider=provider, status="degraded", message=f"Status {resp.status_code}", checked_at=datetime.now())
        except Exception as e: return HealthCheckResponse(provider=provider, status="down", message=str(e), checked_at=datetime.now())
    
    elif provider == "telnyx":
        key = os.getenv("TELNYX_API_KEY")
        if not key: return HealthCheckResponse(provider=provider, status="down", message="No API key", checked_at=datetime.now())
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.telnyx.com/v2/balance", headers={"Authorization": f"Bearer {key}"}, timeout=10.0)
                return HealthCheckResponse(provider=provider, status="operational" if resp.status_code == 200 else "degraded", message="Success" if resp.status_code == 200 else f"Status {resp.status_code}", checked_at=datetime.now())
        except Exception as e: return HealthCheckResponse(provider=provider, status="down", message=str(e), checked_at=datetime.now())

    elif provider == "livekit":
        url, key, secret = os.getenv("LIVEKIT_URL"), os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")
        if not all([url, key, secret]): return HealthCheckResponse(provider=provider, status="down", message="Missing credentials", checked_at=datetime.now())
        try:
            from livekit import api
            lk_api = api.LiveKitAPI(url, key, secret)
            # Simple list rooms to verify connection
            await lk_api.room.list_rooms(api.ListRoomsRequest())
            await lk_api.aclose()
            return HealthCheckResponse(provider=provider, status="operational", message="Connected", checked_at=datetime.now())
        except Exception as e: return HealthCheckResponse(provider=provider, status="down", message=str(e), checked_at=datetime.now())
    
    return HealthCheckResponse(provider=provider, status="operational", message="Auth-only or per-user provider", checked_at=datetime.now())
