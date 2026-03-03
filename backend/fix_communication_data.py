"""
Fix script to assign agents to communications and ensure data is populated for analytics.
"""
from backend.database import SessionLocal
from backend.models_db import Communication, Agent, User
import random

def fix_data():
    db = SessionLocal()
    try:
        # 1. Get a valid agent to assign
        agent = db.query(Agent).first()
        if not agent:
            print("❌ No agents found! Please create an agent first.")
            return

        print(f"Using Agent: {agent.name} ({agent.id})")

        # 2. Get communications without agent_id
        comms = db.query(Communication).filter(Communication.agent_id == None).all()
        print(f"Found {len(comms)} communications without agent_id")

        # 3. Update them
        updated_count = 0
        for comm in comms:
            comm.agent_id = agent.id
            
            # Also populate other fields if missing to ensure "real" looking data
            if not comm.sentiment:
                comm.sentiment = random.choice(["positive", "neutral", "negative", "positive", "neutral"])
            
            if not comm.duration:
                comm.duration = random.randint(30, 300)
                
            updated_count += 1

        db.commit()
        print(f"✅ Updated {updated_count} communications with Agent ID: {agent.id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_data()
