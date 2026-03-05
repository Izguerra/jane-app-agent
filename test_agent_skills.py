import asyncio
from backend.database import SessionLocal
from backend.models_db import Agent
from backend.services.skill_service import SkillService

def test():
    db = SessionLocal()
    agent_id = "agnt_000VCRoP3S1834dms8YCdys6m8P"
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    print(f"Agent: {agent.name}")
    
    svc = SkillService()
    skills = svc.get_skills_for_agent(db, agent_id)
    print(f"Enabled skills: {[s.slug for s in skills]}")

if __name__ == "__main__":
    test()
