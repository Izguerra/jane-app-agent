
from backend.database import engine, Base
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE conversation_messages ADD COLUMN communication_id INTEGER REFERENCES communications(id);"))
            conn.commit()
            print("Successfully added communication_id column")
        except Exception as e:
            if "duplicate column" in str(e):
                print("Column already exists")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    add_column()
