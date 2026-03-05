
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load from root .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("No DB URL found")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("\n--- Users ---")
    users = conn.execute(text("SELECT id, email FROM users")).fetchall()
    for u in users:
        print(u)

    print("\n--- Teams ---")
    teams = conn.execute(text("SELECT id, name FROM teams")).fetchall()
    for t in teams:
        print(t)

    print("\n--- Team Members ---")
    members = conn.execute(text("SELECT user_id, team_id, role FROM team_members")).fetchall()
    for m in members:
        print(m)

    print("\n--- Workspaces ---")
    workspaces = conn.execute(text("SELECT id, team_id FROM workspaces")).fetchall()
    for w in workspaces:
        print(w)
        
    if not workspaces:
        print("\n[ALERT] No workspaces found! This explains the 404.")
