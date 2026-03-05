from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

try:
    with engine.begin() as conn:
        print("Adding welcome_message column to agent_settings...")
        # Check if column exists first
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='agent_settings' AND column_name='welcome_message'"))
        if not result.fetchone():
            conn.execute(text("ALTER TABLE agent_settings ADD COLUMN welcome_message TEXT"))
            print("Column added successfully.")
        else:
            print("Column already exists.")
            
except Exception as e:
    print(f"Error: {e}")

