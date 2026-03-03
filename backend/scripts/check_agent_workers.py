import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
     DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def check_agent(agent_id):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name, allowed_worker_types FROM agents WHERE id = :id"), {"id": agent_id}).fetchone()
        if result:
            print(f"Agent: {result[0]}")
            print(f"Allowed Workers: {result[1]}")
        else:
            print("Agent not found")

def list_instances():
    with engine.connect() as conn:
        print("\n--- Worker Instances ---")
        result = conn.execute(text("SELECT id, status, container_id, connection_url, updated_at FROM worker_instances ORDER BY updated_at DESC")).fetchall()
        for row in result:
            print(f"ID: {row[0]}, Status: {row[1]}, Container: {row[2]}, URL: {row[3]}, Updated: {row[4]}")

if __name__ == "__main__":
    check_agent("agnt_000VA6fCM7ooHx7VALTwm40ed8")
    list_instances()
