from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.begin() as conn:
        # Update User 2 to be in Team 1
        conn.execute(text("UPDATE team_members SET team_id = 1 WHERE user_id = 2"))
        print("Updated User 2 to Team 1")
        
        # Also update the users table if I added a team_id column there? No, I verified it doesn't exist.
        
        # Verify
        result = conn.execute(text("SELECT user_id, team_id FROM team_members WHERE user_id = 2"))
        for row in result:
            print(f"User 2 is now in Team {row[1]}")

except Exception as e:
    print(f"Error: {e}")

