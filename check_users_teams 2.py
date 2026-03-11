from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("\n--- USERS & TEAMS ---")
        query = text("""
            SELECT u.id, u.email, tm.team_id, t.name as team_name
            FROM users u
            JOIN team_members tm ON u.id = tm.user_id
            JOIN teams t ON tm.team_id = t.id
        """)
        result = conn.execute(query)
        for row in result:
            print(row)
except Exception as e:
    print(f"Error: {e}")

