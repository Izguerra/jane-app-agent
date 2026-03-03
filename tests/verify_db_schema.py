
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

# Load from root .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

if not os.getenv("DATABASE_URL"):
    # Try backend/.env
    backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', '.env')
    if os.path.exists(backend_env):
        print(f"Loading {backend_env}")
        load_dotenv(backend_env)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    print("CRITICAL: DATABASE_URL and POSTGRES_URL not found.")
    exit(1)

# Fix postgres:// legacy schema
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Mask password for printing
safe_url = DATABASE_URL
if "@" in safe_url:
    part1 = safe_url.split("@")[1]
    safe_url = "postgresql://*****@" + part1

print(f"Inspecting DB: {safe_url}")

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print("Tables:", tables)
    
    expected_types = {
        'workspaces': {'id': 'VARCHAR', 'team_id': 'VARCHAR'},
        'teams': {'id': 'VARCHAR'},
        'communications': {'id': 'VARCHAR', 'workspace_id': 'VARCHAR'},
        'agent_settings': {'id': 'VARCHAR', 'workspace_id': 'VARCHAR'},
        'integrations': {'id': 'VARCHAR', 'workspace_id': 'VARCHAR'}
    }

    errors = []
    
    for table_name in expected_types:
        if table_name in tables:
            print(f"Checking {table_name}...")
            columns = inspector.get_columns(table_name)
            col_map = {c['name']: str(c['type']) for c in columns}
            
            for col, expected_type in expected_types[table_name].items():
                actual_type = col_map.get(col, "MISSING")
                # Postgres VARCHAR might appear as VARCHAR(20) or similar
                if expected_type in actual_type:
                    print(f"  [OK] {col}: {actual_type}")
                else:
                    print(f"  [FAIL] {col}: Expected {expected_type}, got {actual_type}")
                    errors.append(f"{table_name}.{col}")
        else:
             print(f"[FAIL] Table {table_name} NOT FOUND")
             errors.append(table_name)
             
    if errors:
        print(f"\nSchema Verification FAILED. Mismatches in: {', '.join(errors)}")
        exit(1)
    else:
        print("\nSchema Verification PASSED.")
        exit(0)

except Exception as e:
    print(f"Error: {e}")
    exit(1)
