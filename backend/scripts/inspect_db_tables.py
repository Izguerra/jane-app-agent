
import sys
import os
from sqlalchemy import inspect, text

sys.path.append(os.getcwd())

from backend.database import engine

def inspect_db():
    print("Connecting to DB...")
    try:
        # 1. Inspect Tables
        insp = inspect(engine)
        tables = insp.get_table_names()
        print(f"Tables found ({len(tables)}):")
        for t in tables:
            print(f" - {t}")
            
        if "worker_instances" in tables:
            print("✅ 'worker_instances' table FOUND in metadata inspector.")
            columns = [c['name'] for c in insp.get_columns("worker_instances")]
            print(f"   Columns: {columns}")
        else:
            print("❌ 'worker_instances' table NOT FOUND in metadata inspector.")

        # 2. Raw SQL Check
        with engine.connect() as conn:
            print("\nAttempting raw SELECT...")
            try:
                result = conn.execute(text("SELECT count(*) FROM worker_instances"))
                count = result.scalar()
                print(f"✅ Raw SELECT successful. Count: {count}")

                # 3. Raw INSERT Check
                print("Attempting raw INSERT...")
                import uuid
                test_id = str(uuid.uuid4())
                conn.execute(text(f"""
                    INSERT INTO worker_instances (id, workspace_id, name, worker_type) 
                    VALUES ('{test_id}', 'test_wrk', 'Test Bot', 'openclaw')
                """))
                print("✅ Raw INSERT successful.")
                conn.commit() # Commit to verifying it persists (or rolls back if error)

            except Exception as e:
                print(f"❌ Raw SQL Operation failed: {e}")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    inspect_db()
