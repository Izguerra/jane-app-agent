from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("\n--- TABLES ---")
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        for row in result:
            print(row[0])
except Exception as e:
    print(f"Error: {e}")

