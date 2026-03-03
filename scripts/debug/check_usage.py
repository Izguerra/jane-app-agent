from backend.database import SessionLocal
from backend.models_db import Workspace, User

db = SessionLocal()
try:
    # Get the first user (assuming it's the one we are using)
    user = db.query(User).first()
    if user:
        print(f"User: {user.email}, Team ID: {user.team_id}")
        workspace = db.query(Workspace).filter(Workspace.team_id == user.team_id).first()
        if workspace:
            print(f"Workspace ID: {workspace.id}")
            print(f"Voice Minutes Used: {workspace.voice_minutes_this_month}")
        else:
            print("No workspace found for this team.")
    else:
        print("No user found.")
finally:
    db.close()
