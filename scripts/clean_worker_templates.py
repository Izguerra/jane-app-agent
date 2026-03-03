import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def list_templates():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, slug, category, is_active FROM worker_templates"))
        rows = result.fetchall()
        print(f"Found {len(rows)} templates:")
        for row in rows:
            print(f"ID: {row[0]} | Name: {row[1]} | Slug: {row[2]} | Category: {row[3]} | Active: {row[4]}")

if __name__ == "__main__":
    list_templates()
