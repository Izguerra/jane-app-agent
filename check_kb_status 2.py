from backend.database import get_db
from sqlalchemy import text
import sys

# Mocking the app context to use get_db
# Actually better to just make a direct connection or use the session
from backend.database import SessionLocal

def check_status():
    db = SessionLocal()
    try:
        # Check Workspaces for the team
        team_id = "tm_ead0lel3nkag"
        print(f"Checking workspaces for team: {team_id}")
        workspaces = db.execute(text("SELECT id, name, created_at FROM workspaces WHERE team_id = :tid"), {"tid": team_id}).fetchall()
        for ws in workspaces:
            print(f"Found Workspace: {ws[0]} - {ws[1]} (Created: {ws[2]})")

        # Find the most recent source
        result = db.execute(text("""
            SELECT id, workspace_id, name, status, document_count, error_message, config
            FROM knowledge_base_sources
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()
        
        if result:
            print(f"\nMost Recent Source:")
            print(f"Source ID: {result[0]}")
            print(f"Workspace ID: {result[1]}")
            print(f"Name: {result[2]}")
            print(f"Status: {result[3]}")
            print(f"Doc Count: {result[4]}")
            print(f"Error: {result[5]}")
            print(f"Config: {result[6]}")
            
            # Check documents count for this source
            # docs = db.execute(text("""
            #     SELECT COUNT(*) FROM knowledge_base_documents WHERE source_id = :sid
            # """), {"sid": result[0]}).scalar()
            # print(f"Actual Documents in DB: {docs}")
            
        else:
            print("No sources found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_status()
