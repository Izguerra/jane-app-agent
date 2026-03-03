
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models_db import Agent
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_db_update():
    db = SessionLocal()
    try:
        # Get the first agent
        agent = db.query(Agent).first()
        if not agent:
            print("No agents found in DB")
            return
        
        print(f"Found agent: {agent.id}")
        print(f"Current allowed_worker_types: {agent.allowed_worker_types}")
        
        # Try to update
        agent.allowed_worker_types = ["test_worker"]
        agent.settings = agent.settings or {}
        agent.settings["test_key"] = "test_value"
        
        db.commit()
        print("Update successful!")
        
        # Verify
        db.refresh(agent)
        print(f"New allowed_worker_types: {agent.allowed_worker_types}")
        print(f"New settings keys: {agent.settings.keys() if agent.settings else 'None'}")
        
    except Exception as e:
        print(f"Update FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_db_update()
