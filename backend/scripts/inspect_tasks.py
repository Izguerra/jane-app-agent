import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
     DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def inspect_tasks():
    with engine.connect() as conn:
        print("\n--- Recent Tasks ---")
        result = conn.execute(text("SELECT id, status, worker_type, workspace_id, input_data FROM worker_tasks ORDER BY created_at DESC LIMIT 5")).fetchall()
        for row in result:
            print(f"ID: {row[0]}")
            print(f"Status: {row[1]}")
            print(f"Type: {row[2]}")
            print(f"Workspace: {row[3]}")
            print(f"Input: {row[4]}")
            print("-" * 20)

if __name__ == "__main__":
    inspect_tasks()
