from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.auth import get_current_user, AuthUser
from backend.database import get_db
from .models import GeneralSettings

router = APIRouter(tags=["Admin - General Settings"])

@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get general platform settings."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = db.execute(text("SELECT * FROM admin_settings LIMIT 1")).fetchone()
    if not result: raise HTTPException(status_code=404, detail="Settings not found")
    
    return GeneralSettings(
        company_name=result[1], support_email=result[2],
        default_language=result[3], timezone=result[4]
    )

@router.put("/general", response_model=GeneralSettings)
async def update_general_settings(
    settings: GeneralSettings,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update general platform settings."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("""
        UPDATE admin_settings 
        SET company_name = :n, support_email = :e, default_language = :l, timezone = :t
    """), {"n": settings.company_name, "e": settings.support_email, "l": settings.default_language, "t": settings.timezone})
    db.commit()
    return settings
