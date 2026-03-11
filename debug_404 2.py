from backend.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    team_id = "tm_ead0lel3nkag"
    print(f"Checking Team: {team_id}")
    team = db.execute(text("SELECT id, name FROM teams WHERE id = :id"), {"id": team_id}).fetchone()
    print(f"Team Found: {team}")
    
    if team:
        print(f"Checking Workspace for Team: {team_id}")
        ws = db.execute(text("SELECT id, name FROM workspaces WHERE team_id = :id"), {"id": team_id}).fetchone()
        print(f"Workspace Found: {ws}")
    else:
        print("Team does not exist! This explains the issue.")
        
finally:
    db.close()
