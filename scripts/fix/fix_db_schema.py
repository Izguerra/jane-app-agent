from backend.database import engine, Base
from sqlalchemy import inspect, text
from backend.models_db import Workspace

def check_and_fix_schema():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('workspaces')]
    
    print(f"Current columns in workspaces: {columns}")
    
    missing_columns = []
    if 'conversations_this_month' not in columns:
        missing_columns.append("conversations_this_month INTEGER DEFAULT 0")
    if 'voice_minutes_this_month' not in columns:
        missing_columns.append("voice_minutes_this_month INTEGER DEFAULT 0")
        
    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        with engine.connect() as conn:
            for col_def in missing_columns:
                print(f"Adding column: {col_def}")
                conn.execute(text(f"ALTER TABLE workspaces ADD COLUMN {col_def}"))
            conn.commit()
        print("Schema updated successfully.")
    else:
        print("Schema is up to date.")

if __name__ == "__main__":
    check_and_fix_schema()
