from backend.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- Workspaces ---")
    workspaces = db.execute(text("SELECT id, name FROM workspaces")).fetchall()
    for w in workspaces:
        print(f"ID: {w[0]}, Name: {w[1]}")

    print("\n--- Knowledge Base Sources ---")
    result = db.execute(text("SELECT id, workspace_id, name, status, document_count FROM knowledge_base_sources")).fetchall()
    
    if not result:
        print("No sources found.")
        
    for row in result:
        print(f"ID: {row[0]}")
        print(f"  Workspace: {row[1]}")
        print(f"  Name: {row[2]}")
        print(f"  Status: {row[3]}")
        print(f"  Docs: {row[4]}")
        print("-" * 20)
finally:
    db.close()
