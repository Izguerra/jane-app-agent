"""
Database query helpers for authentication and team management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

def get_team_for_user(db: Session, user_id: str) -> Optional[str]:
    """
    Get the team_id for a given user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        team_id if user is in a team, None otherwise
    """
    # Query the team_members table to find user's team
    # This assumes the Postgres schema from the Next.js app
    result = db.execute(
        text("""
        SELECT team_id 
        FROM team_members 
        WHERE user_id = :user_id 
        LIMIT 1
        """),
        {"user_id": user_id}
    ).fetchone()
    
    if result:
        return result[0]
    
    return None

def get_user_role(db: Session, user_id: str, team_id: str) -> Optional[str]:
    """
    Get the role of a user in a specific team.
    
    Args:
        db: Database session
        user_id: User ID
        team_id: Team ID
        
    Returns:
        Role string (e.g. 'owner', 'member') or None
    """
    # First check if user is a platform admin
    admin_check = db.execute(
        text("SELECT role FROM users WHERE id = :user_id LIMIT 1"),
        {"user_id": user_id}
    ).fetchone()

    if admin_check and admin_check[0] == 'supaagent_admin':
        return 'supaagent_admin'

    # Otherwise check team role
    result = db.execute(
        text("""
        SELECT role 
        FROM team_members 
        WHERE user_id = :user_id AND team_id = :team_id
        LIMIT 1
        """),
        {"user_id": user_id, "team_id": team_id}
    ).fetchone()
    
    if result:
        return result[0]
    
    return None
