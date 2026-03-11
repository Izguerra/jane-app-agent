from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models_db import Base, Agent, AgentSkill, Communication
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./supaagent.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- LATEST AGENTS ---")
agents = db.query(Agent).order_by(Agent.created_at.desc()).limit(3).all()
for a in agents:
    print(f"Agent ID: {a.id}, Name: {a.name}, Type: {a.settings.get('agent_type') if a.settings else 'N/A'}")
    if a.settings and a.settings.get('agent_type') == 'personal':
        print(f"  Profile: {a.settings.get('owner_name')}, {a.settings.get('personal_location')}")
    
    skills = db.query(AgentSkill).filter(AgentSkill.agent_id == a.id, AgentSkill.enabled == True).count()
    print(f"  Enabled Skills Count: {skills}")

print("\n--- LATEST COMMUNICATIONS ---")
comms = db.query(Communication).order_by(Communication.started_at.desc()).limit(5).all()
for c in comms:
    print(f"Comm ID: {c.id}, Type: {c.type}, Channel: {c.channel}, Status: {c.status}")

