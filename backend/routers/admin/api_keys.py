import secrets
import hashlib
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.auth import get_current_user, AuthUser
from backend.database import get_db
from .models import APIKey, APIKeyCreate, APIKeyResponse

router = APIRouter(tags=["Admin - API Keys"])

@router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of API keys."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.execute(text("""
        SELECT id, name, key_prefix, last_used_at, created_at
        FROM api_keys ORDER BY created_at DESC
    """)).fetchall()
    
    return [
        APIKey(id=str(row[0]), name=row[1], key_prefix=row[2], last_used_at=row[3], created_at=row[4])
        for row in results
    ]

@router.post("/api-keys", response_model=APIKeyResponse)
async def generate_api_key(
    key_data: APIKeyCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    key_prefix = api_key[:12] + "..."
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    key_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO api_keys (id, name, key_hash, key_prefix, created_at)
        VALUES (:id, :name, :key_hash, :key_prefix, :created_at)
    """), {"id": key_id, "name": key_data.name, "key_hash": key_hash, "key_prefix": key_prefix, "created_at": datetime.now()})
    db.commit()
    
    return APIKeyResponse(id=key_id, name=key_data.name, key=api_key, key_prefix=key_prefix)

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    if current_user.role not in ["owner", "supaagent_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": key_id})
    db.commit()
    return {"message": "API key deleted successfully"}
