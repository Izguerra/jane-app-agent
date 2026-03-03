import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Workspace, Team, User
from dotenv import load_dotenv

load_dotenv()

def check_access(workspace_id):
    db = SessionLocal()
    try:
        print(f"--- Debugging Access for Workspace: {workspace_id} ---")
        
        # 1. Check Workspace
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            print(f"ERROR: Workspace {workspace_id} NOT FOUND in DB.")
            return

        print(f"Workspace Name: {workspace.name}")
        print(f"Workspace Team ID: {workspace.team_id}")
        
        # 2. Check Team
        team = db.query(Team).filter(Team.id == workspace.team_id).first()
        if team:
            print(f"Team Found: {team.name} (ID: {team.id})")
        else:
            print(f"ERROR: Team {workspace.team_id} NOT FOUND.")
            
        # 3. Check Users in Team
        users = db.query(User).all()
        print(f"\n--- Users in System ---")
        for u in users:
            # Check team member table if needed, or if user has team_id directly (DB schema dependent)
            # Assuming User table has team_id for simplicity based on auth.py logic, or we check team_members
            is_member = False
            
            # Simple check if there's a team_members table or direct link
            # Let's try to query TeamMember if it exists, otherwise assume direct link
            try:
                from backend.models_db import TeamMember
                tm = db.query(TeamMember).filter(TeamMember.user_id == u.id, TeamMember.team_id == workspace.team_id).first()
                if tm:
                    is_member = True
                    role = tm.role
                else:
                    role = "N/A"
            except:
                # Fallback to direct check if simple schema
                is_member = (str(u.team_id) == str(workspace.team_id)) if hasattr(u, 'team_id') else False
                role = u.role
            
            if is_member:
                print(f"User: {u.email} (ID: {u.id}) - ROLE: {role} -> HAS ACCESS")
            else:
                pass
                # print(f"User: {u.email} - No Access (Team mismatch)")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_access.py <workspace_id>")
    else:
        check_access(sys.argv[1])
