
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def inspect_table(table_name):
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    print(f"\n--- COLUMNS FOR {table_name} ---")
    for column in columns:
        print(f"Name: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Default: {column.get('default')}")

if __name__ == "__main__":
    inspect_table('agents')
