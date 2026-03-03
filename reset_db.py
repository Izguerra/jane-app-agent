from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.begin() as conn:
        print("Truncating tables...")
        # Truncate main tables and cascade to dependent tables
        conn.execute(text("TRUNCATE TABLE users, teams, workspaces, agent_settings, communication_logs RESTART IDENTITY CASCADE"))
        print("Successfully wiped all users, teams, workspaces, settings, and logs.")
        
except Exception as e:
    print(f"Error: {e}")

