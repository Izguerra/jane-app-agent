from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.auth import get_current_user, AuthUser
from backend.database import get_db
from .models import SecurityOverview, ActiveSession

router = APIRouter(tags=["Admin - Security"])

@router.get("/security", response_model=SecurityOverview)
async def get_security_overview(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security overview."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db.execute(text("SELECT two_factor_enabled FROM admin_settings LIMIT 1")).fetchone()
    sessions_count = db.execute(text("SELECT COUNT(*) FROM active_sessions")).fetchone()[0]
    
    return SecurityOverview(
        two_factor_enabled=settings[0] if settings else False,
        password_last_changed=None,
        active_sessions_count=sessions_count
    )

@router.get("/security/sessions", response_model=List[ActiveSession])
async def get_active_sessions(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of active sessions."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.execute(text("""
        SELECT id, device_name, location, ip_address, last_active_at, created_at
        FROM active_sessions ORDER BY last_active_at DESC
    """)).fetchall()
    
    return [
        ActiveSession(id=str(row[0]), device_name=row[1], location=row[2], ip_address=row[3], last_active_at=row[4], created_at=row[5])
        for row in results
    ]

@router.delete("/security/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an active session."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("DELETE FROM active_sessions WHERE id = :id"), {"id": session_id})
    db.commit()
    return {"message": "Session revoked successfully"}
