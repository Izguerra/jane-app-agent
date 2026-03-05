from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:54322/postgres')
with engine.connect() as conn:
    tables = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).fetchall()
    print('\n'.join([t[0] for t in tables]))
