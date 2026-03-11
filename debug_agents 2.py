from backend.database import SessionLocal
from backend.models_db import Agent, Workspace, Team
from sqlalchemy import text

def debug_db():
    db = SessionLocal()
    try:
        print("\n=== WORKSPACES ===")
        workspaces = db.query(Workspace).all()
        for w in workspaces:
            print(f"ID: {w.id}, Name: {w.name}, Team ID: {w.team_id}")

        print("\n=== USERS (Top 10) ===")
        # Raw SQL because TeamMember model might not be exported or I missed it
        result = db.execute(text("SELECT u.email, tm.team_id, tm.role FROM users u JOIN team_members tm ON u.id = tm.user_id LIMIT 20"))
        for row in result:
            print(f"User: {row[0]}, Team ID: {row[1]}, Role: {row[2]}")

        print("\n=== AGENTS ===")
        agents = db.query(Agent).all()
        for a in agents:
            print(f"ID: {a.id}, Name: {a.name}, Workspace ID: {a.workspace_id}, Active: {a.is_active}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_db()
