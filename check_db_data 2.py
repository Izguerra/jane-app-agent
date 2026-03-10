from sqlalchemy import create_engine, text
import os

# Hardcoded for diagnosis since I know it works
db_url = "postgresql://postgres:postgres@localhost:54322/postgres"

engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("\n--- USERS ---")
        result = conn.execute(text("SELECT id, email, team_id FROM users"))
        for row in result:
            print(row)

        print("\n--- WORKSPACES (Clinics) ---")
        result = conn.execute(text("SELECT id, name, team_id FROM clinics"))
        for row in result:
            print(row)

        print("\n--- SETTINGS ---")
        result = conn.execute(text("SELECT id, workspace_id, voice_id FROM agent_settings"))
        for row in result:
            print(row)
            
        print("\n--- COMMUNICATION LOGS ---")
        result = conn.execute(text("SELECT id, workspace_id, status FROM communication_logs LIMIT 5"))
        for row in result:
            print(row)

except Exception as e:
    print(f"Error: {e}")
