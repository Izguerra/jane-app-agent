from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("\n--- AGENT SETTINGS ---")
        result = conn.execute(text("SELECT id, workspace_id, voice_id FROM agent_settings"))
        for row in result:
            print(row)
except Exception as e:
    print(f"Error: {e}")

