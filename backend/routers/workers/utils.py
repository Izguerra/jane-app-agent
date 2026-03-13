from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.models_db import Workspace, Team, TeamMember
from backend.auth import AuthUser

def verify_workspace_access(db: Session, user: AuthUser, workspace_id: str):
    """
    Ensure the user belongs to the team that owns the workspace.
    """
    if not workspace_id:
        return
        
    workspace = None
    if workspace_id.startswith("tm_") or workspace_id.startswith("org_"):
        workspace = db.query(Workspace).filter(Workspace.team_id == workspace_id).first()
    else:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    if not workspace:
        if workspace_id.startswith("tm_") or workspace_id.startswith("org_"):
             team = db.query(Team).filter(Team.id == workspace_id).first()
             if team:
                 from backend.database import generate_workspace_id
                 workspace = Workspace(
                     id=generate_workspace_id(),
                     team_id=team.id,
                     name=f"Workspace for {team.id}",
                     is_active=True
                 )
                 db.add(workspace)
                 db.commit()
                 db.refresh(workspace)
             else:
                 raise HTTPException(status_code=404, detail="Workspace not found (Invalid Team ID)")
        else:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
    if str(workspace.team_id) != str(user.team_id):
        membership = db.query(TeamMember).filter(
            TeamMember.user_id == user.id,
            TeamMember.team_id == workspace.team_id
        ).first()

        if not membership and user.role != "supaagent_admin":
             raise HTTPException(status_code=403, detail=f"Not authorized. User team: {user.team_id}, Workspace team: {workspace.team_id}")
