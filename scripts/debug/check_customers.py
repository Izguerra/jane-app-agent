from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:54322/postgres')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) as count FROM customers')).fetchone()
    print(f'Total customers in database: {result[0]}')
    
    # Show sample customers
    customers = conn.execute(text('SELECT id, email, workspace_id FROM customers LIMIT 5')).fetchall()
    print('\nSample customers:')
    for c in customers:
        print(f'  - {c.email} (workspace: {c.workspace_id})')
