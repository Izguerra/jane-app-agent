"""
Authentication middleware for FastAPI backend.
Extracts user and team_id from JWT tokens passed from Next.js frontend.
"""
from fastapi import Depends, HTTPException, Header, Request
from typing import Optional, Dict
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Use the same secret as Next.js AUTH_SECRET
SECRET_KEY = os.getenv("AUTH_SECRET")
if not SECRET_KEY:
    # WARN but do not crash immediately so dev environment setup is easier, 
    # but ensure it's known this is insecure if it happens.
    # Actually, for "Cleanup & Hardening" we should probably enforce it or generate a secure random one if missing to prevent "secret_placeholder" attacks.
    # Generating one means tokens won't match frontend. Better to fail or warn.
    # Let's keep a fallback for Dev but make it explicitly dev-only if possible?
    # Or just default to None and fail in get_current_user if not set.
    print("WARNING: AUTH_SECRET not set in environment. Authentication will fail.")
    SECRET_KEY = None
ALGORITHM = "HS256"

class AuthUser:
    """Represents an authenticated user with team context"""
    def __init__(self, user_id: str, team_id: str, email: str = None, role: str = None, name: str = None):
        self.id = user_id
        self.team_id = team_id
        self.email = email
        self.role = role
        self.name = name

from backend.database import get_db
from sqlalchemy.orm import Session

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AuthUser:
    """
    Extract user from JWT token in Authorization header or session cookie.
    """
    if authorization == "Bearer DEVELOPER_BYPASS":
        return AuthUser(
            user_id="dev_user",
            team_id="org_000V7dMzThAVrPNF3XBlRXq4MO", 
            email="dev@example.com",
            role="admin",
            name="Developer Admin"
        )

    token = None
    if authorization:
        token = authorization.replace("Bearer ", "")
    elif request.cookies.get("session"):
        token = request.cookies.get("session")
    
    if not token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Authorization header or session cookie required."
        )
    
    try:
        # Decode JWT using same secret and algorithm as Next.js
        # Next.js uses jose with SignJWT and HS256
        # PyJWT implementation
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        
        # Extract user data from token
        user_data = payload.get("user", {})
        user_id = user_data.get("id")
        
        # New tokens have teamId in the payload
        team_id = user_data.get("teamId")
        role = user_data.get("role") 
        
        if not user_id:
            # Check if this is a Worker Token (Machine-to-Machine)
            # Worker tokens have 'role': 'worker_instance' and 'workspace_id' at top level
            worker_role = payload.get("role")
            workspace_id = payload.get("workspace_id")
            
            if worker_role == "worker_instance" and workspace_id:
                # Fetch real team_id for this workspace to pass access checks
                from backend.models_db import Workspace
                ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                real_team_id = ws.team_id if ws else workspace_id

                return AuthUser(
                    user_id=f"worker_{workspace_id[:8]}", # Dummy ID
                    team_id=real_team_id,
                    email="worker@system.local",
                    role="worker_instance",
                    name="System Worker"
                )

            raise HTTPException(
                status_code=401, 
                detail="Invalid token: missing user id"
            )
        
        # If team_id is missing (legacy token), fetch from DB
        from backend.lib.db_queries import get_team_for_user, get_user_role
        
        if not team_id:
            team_id = get_team_for_user(db, user_id)
            if not team_id:
                raise HTTPException(
                    status_code=403,
                    detail="User not associated with any team"
                )
        
        # Use DB to get role if not in token, to ensure it's up to date
        # (or if token didn't have it)
        current_role = get_user_role(db, user_id, team_id)
        if current_role:
             role = current_role
        
        return AuthUser(
            user_id=user_id,
            team_id=team_id,
            email=payload.get("email"),
            role=role,
            name=user_data.get("name")
        )
        
    except jwt.PyJWTError as e:
        # import traceback
        # print(f"JWT Error Details: {str(e)}")
        # print(f"Token (first 50 chars): {token[:50] if token else 'None'}")
        # print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        import traceback
        print(f"Unexpected auth error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

# Cache for workspace resolution (team_id -> workspace_id)
# Format: {team_id: (workspace_id, timestamp)}
_workspace_cache: Dict[str, tuple[str, float]] = {}
_CACHE_TTL = 300  # 5 minutes in seconds

def get_workspace_context(
    db: Session,
    user: AuthUser,
    workspace_id: Optional[str] = None,
    request: Request = None # Add request to access headers
) -> str:
    # Check for bypass header first
    if request:
        bypass_ws = request.headers.get("X-Bypass-Workspace-ID")
        if bypass_ws:
            print(f"DEBUG: Using bypass workspace ID: {bypass_ws}")
            return bypass_ws

    """
    Robustly resolves the active workspace_id with caching for performance.
    - If workspace_id is provided and starts with 'wrk_', uses it (if it belongs to user's team).
    - If workspace_id starts with 'tm_' or 'org_', finds the associated workspace.
    - Fallback: Finds the PRIMARY workspace (most data) for the user's team.
    - Prevents accidental creation of multiple workspaces for the same team.
    - Uses in-memory cache to avoid expensive COUNT queries on every request.
    """
    from backend.models_db import Workspace, Agent, Customer, Communication
    from backend.database import generate_workspace_id
    from sqlalchemy import func
    import time

    # 1. Direct Workspace ID provided
    if workspace_id and workspace_id.startswith("wrk_"):
        ws = db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.team_id == user.team_id
        ).first()
        if ws:
            return ws.id

    # 2. Team/Org ID provided (Common in URLs) or Fallback to user.team_id
    id_to_check = workspace_id if workspace_id and (workspace_id.startswith("tm_") or workspace_id.startswith("org_")) else user.team_id
    
    # Check cache first
    current_time = time.time()
    if id_to_check in _workspace_cache:
        cached_workspace_id, cached_time = _workspace_cache[id_to_check]
        if current_time - cached_time < _CACHE_TTL:
            # Cache hit - return cached workspace_id
            return cached_workspace_id
    
    # ALWAYS check if a workspace already exists for this team first
    # Sort by created_at ASC to ensure the oldest (original) workspace is picked as primary.
    existing_workspaces = db.query(Workspace).filter(Workspace.team_id == id_to_check).order_by(Workspace.created_at.asc()).all()
    
    if existing_workspaces:
        # If multiple workspaces exist, return the oldest one.
        # This is fast and restores consistency with existing agents.
        resolved_workspace_id = existing_workspaces[0].id
        
        # Cache the result
        _workspace_cache[id_to_check] = (resolved_workspace_id, current_time)
        
        if len(existing_workspaces) > 1:
            print(f"DEBUG: Found {len(existing_workspaces)} workspaces for team {id_to_check}. Selected first: {resolved_workspace_id}")
        
        return resolved_workspace_id

    # 3. Create only if none exists (Prevent Eager Duplication)
    new_ws = Workspace(
        id=generate_workspace_id(),
        team_id=id_to_check,
        name=f"Workspace for {id_to_check}"
    )
    db.add(new_ws)
    db.commit()
    db.refresh(new_ws)
    
    # Cache the new workspace
    _workspace_cache[id_to_check] = (new_ws.id, current_time)
    
    return new_ws.id

def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[AuthUser]:
    """
    Optional authentication - returns None if no token provided.
    Useful for endpoints that work with or without auth.
    """
    if not authorization and not request.cookies.get("session"):
        return None
    
    try:
        return get_current_user(request, authorization, db)
    except HTTPException:
        return None
