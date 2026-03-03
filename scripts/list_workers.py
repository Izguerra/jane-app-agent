from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import SessionLocal

def list_workers():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT name, slug, id, category FROM worker_templates ORDER BY name")).fetchall()
        print(f"{'NAME':<30} | {'SLUG':<30} | {'ID'}")
        print("-" * 100)
        for row in result:
             print(f"{row[0]:<30} | {row[1]:<30} | {row[2]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_workers()
