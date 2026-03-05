from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("\n--- LOGS for Workspace 1 ---")
        result = conn.execute(text("SELECT id, status, start_time FROM communication_logs WHERE workspace_id = 1"))
        rows = result.fetchall()
        if not rows:
            print("No logs found for Workspace 1")
        else:
            for row in rows:
                print(row)
                
        print("\n--- LOGS for Workspace 2 ---")
        result = conn.execute(text("SELECT id, status, start_time FROM communication_logs WHERE workspace_id = 2"))
        rows = result.fetchall()
        if not rows:
            print("No logs found for Workspace 2")
        else:
            for row in rows:
                print(row)

except Exception as e:
    print(f"Error: {e}")

