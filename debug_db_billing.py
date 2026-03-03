from backend.database import SessionLocal
from backend.models_db import Workspace, Team, User
from sqlalchemy import text

db = SessionLocal()

workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
user_email = "resguerra75@gmail.com"

print(f"--- Debugging Workspace: {workspace_id} ---")
workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
if workspace:
    print(f"Workspace Found: {workspace.name}")
    print(f"Workspace Team ID: {workspace.team_id}")
    
    team = db.query(Team).filter(Team.id == workspace.team_id).first()
    if team:
        print(f"Team Found (via Workspace): {team.name}")
        print(f"Team ID: {team.id}")
        print(f"Team Stripe Customer ID: {team.stripe_customer_id}")
        print(f"Team Plan Name: {team.plan_name}")
        print(f"Team Sub Status: {team.subscription_status}")
    else:
        print("Team NOT FOUND via Workspace!")
else:
    print("Workspace NOT FOUND")

print(f"\n--- Debugging User: {user_email} ---")
user = db.query(User).filter(User.email == user_email).first()
if user:
    print(f"User Found: {user.id}")
    # User team link might be via team_members table or direct column if simplified
    # Checking team_members
    result = db.execute(text("SELECT team_id FROM team_members WHERE user_id = :uid"), {"uid": user.id}).fetchone()
    if result:
        user_team_id = result[0]
        print(f"User Team ID: {user_team_id}")
        
        user_team = db.query(Team).filter(Team.id == user_team_id).first()
        if user_team:
             print(f"Team Stripe Customer ID (via User): {user_team.stripe_customer_id}")
    else:
        print("User has no team membership")
else:
    print("User NOT FOUND")
