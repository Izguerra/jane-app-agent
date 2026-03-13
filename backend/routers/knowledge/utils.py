from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

def verify_workspace_access(workspace_id: str, current_user: dict, db: Session) -> str:
    """Verify user has access to workspace and resolve Team ID to Workspace ID if needed."""
    real_workspace_id = workspace_id
    
    if workspace_id.startswith(("org_", "tm_")):
        row = db.execute(text("SELECT id, team_id FROM workspaces WHERE team_id = :team_id"), {"team_id": workspace_id}).fetchone()
        if not row:
             from backend.database import generate_workspace_id
             ws_id = generate_workspace_id()
             db.execute(text("INSERT INTO workspaces (id, team_id, name, created_at, updated_at) VALUES (:id, :team_id, :name, NOW(), NOW())"), {
                 "id": ws_id, "team_id": workspace_id, "name": f"Workspace for {workspace_id}"
             })
             db.commit()
             real_workspace_id = ws_id
        else:
             real_workspace_id = row[0]
        
    workspace = db.execute(text("SELECT id, team_id FROM workspaces WHERE id = :id"), {"id": real_workspace_id}).fetchone()
    if not workspace: raise HTTPException(status_code=404, detail="Workspace not found")
        
    if current_user.role in ['supaagent_admin', 'owner'] or current_user.team_id == workspace[1]:
        return real_workspace_id
        
    raise HTTPException(status_code=403, detail="Access denied")
