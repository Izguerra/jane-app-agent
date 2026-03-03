
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from backend.database import engine

with engine.connect() as conn:
    print(f"Checking for user: resguerra75@gmail.com")
    result = conn.execute(text("SELECT * FROM users WHERE email='resguerra75@gmail.com'")).fetchone()
    if result:
        print(f"User found: {result}")
        # Check team
        user_id = result.id
        team_member = conn.execute(text(f"SELECT * FROM team_members WHERE user_id='{user_id}'")).fetchone()
        if team_member:
            print(f"Team Member found: {team_member}")
            team_id = team_member.team_id
            workspace = conn.execute(text(f"SELECT * FROM workspaces WHERE team_id='{team_id}'")).fetchone()
            if workspace:
                print(f"Workspace found: {workspace}")
                # Check agents
                agents = conn.execute(text(f"SELECT * FROM agents WHERE workspace_id='{workspace.id}'")).fetchall()
                print(f"Agents count: {len(agents)}")
            else:
                print(f"NO WORKSPACE found for team_id: {team_id}")
        else:
            print(f"NO TEAM MEMBER found for user_id: {user_id}")
    else:
        print("User NOT found")
