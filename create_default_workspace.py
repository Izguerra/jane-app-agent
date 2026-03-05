from backend.database import SessionLocal, generate_workspace_id
from backend.models_db import Team, Workspace

def create_default():
    db = SessionLocal()
    try:
        # Get seed team
        team = db.query(Team).filter(Team.name == "Test Team").first()
        if not team:
            print("Error: Seed team not found. Run seed.ts first.")
            return

        print(f"Found Team: {team.name} (ID: {team.id})")

        # Check for workspace
        ws = db.query(Workspace).filter(Workspace.team_id == team.id).first()
        if not ws:
            ws_id = generate_workspace_id()
            ws = Workspace(
                id=ws_id,
                team_id=team.id,
                name="Default Workspace",
                description="Auto-generated default workspace"
            )
            db.add(ws)
            db.commit()
            db.refresh(ws)
            print(f"Created Workspace: {ws.name} (ID: {ws.id})")
        else:
            print(f"Existing Workspace: {ws.name} (ID: {ws.id})")

    finally:
        db.close()

if __name__ == "__main__":
    create_default()
