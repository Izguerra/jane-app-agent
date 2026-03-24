import os
import sys

# Add project root to sys.path
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from backend.database import SessionLocal
from backend.services.skill_service import SkillService
from backend.models_db import Agent, Skill, AgentSkill

def test_persistence():
    db = SessionLocal()
    try:
        # 1. Find an agent
        agent = db.query(Agent).first()
        if not agent:
            print("No agents found in database.")
            return
        
        print(f"Testing persistence for Agent: {agent.id} (Workspace: {agent.workspace_id})")
        
        # 2. Get available skills
        skills = SkillService.get_skills_catalog(db, agent.workspace_id)
        if not skills:
            print("No skills found in catalog.")
            return
        
        test_skill = skills[0]
        print(f"Toggling skill: {test_skill.name} ({test_skill.id})")
        
        # 3. Toggle ON
        SkillService.toggle_skill(db, agent.id, test_skill.id, agent.workspace_id, True)
        db.commit()
        
        # 4. Verify
        enabled_skills = SkillService.get_skills_for_agent(db, agent.id)
        is_enabled = any(s.id == test_skill.id for s in enabled_skills)
        print(f"Post-toggle verification (ON): {is_enabled}")
        
        # 5. Toggle OFF
        SkillService.toggle_skill(db, agent.id, test_skill.id, agent.workspace_id, False)
        db.commit()
        
        # 6. Verify Again
        enabled_skills = SkillService.get_skills_for_agent(db, agent.id)
        is_still_enabled = any(s.id == test_skill.id for s in enabled_skills)
        print(f"Post-toggle verification (OFF): {not is_still_enabled}")
        
        if is_enabled and not is_still_enabled:
            print("✅ Skill persistence is WORKING perfectly.")
        else:
            print("❌ Skill persistence is FAILING.")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_persistence()
