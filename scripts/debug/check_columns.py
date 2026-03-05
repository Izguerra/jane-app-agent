from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
engine = create_engine(db_url)

def print_cols(table):
    print(f"\n--- COLUMNS: {table} ---")
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
        for row in result:
            print(row[0])

print_cols('agent_settings')
print_cols('workspaces')
print_cols('communication_logs')

