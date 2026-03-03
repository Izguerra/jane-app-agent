
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Workspace, Team, User

def run():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        teams = db.query(Team).all()
        workspaces = db.query(Workspace).all()

        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"  User: {u.email} (ID: {u.id}, Role: {u.role})")

        print(f"\nTotal Teams: {len(teams)}")
        for t in teams:
            print(f"  Team: {t.name} (ID: {t.id})")

        print(f"\nTotal Workspaces: {len(workspaces)}")
        for w in workspaces:
            print(f"  Workspace: {w.name} (ID: {w.id}, TeamID: {w.team_id})")

    finally:
        db.close()

if __name__ == "__main__":
    run()
