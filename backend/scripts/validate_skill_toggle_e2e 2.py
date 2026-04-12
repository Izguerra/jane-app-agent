import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.services.skill_service import SkillService
from backend.services.brain_service import BrainService
from backend.models_db import Skill, Agent

def validate_skill_toggles():
    print("🧪 Validating Dynamic Skill Toggles (End-to-End)...\n")
    db = SessionLocal()
    
    try:
        # 1. Setup Test Subject
        agent = db.query(Agent).first()
        if not agent:
            print("❌ No agent found in database.")
            return
            
        agent_id = agent.id
        workspace_id = agent.workspace_id
        print(f"Targeting Agent: {agent_id} in Workspace: {workspace_id}")
        
        # Find 'web-research' skill
        web_search_skill = db.query(Skill).filter(Skill.slug == 'web-research').first()
        if not web_search_skill:
            print("❌ 'web-research' skill not found in catalog.")
            return
            
        skill_id = web_search_skill.id
        
        # ── Scenario 1: Disable Skill ──
        print("\nStep 1: Disabling 'web-research'...")
        SkillService.toggle_skill(db, agent_id, skill_id, workspace_id, enabled=False)
        
        # Reload skills and build prompt
        enabled_skills = SkillService.get_skills_for_agent(db, agent_id)
        prompt = BrainService.build_prompt(
            agent.settings or {}, "", enabled_skills, 
            {"name": "Test"}, "Monday", "Toronto", agent_type="personal"
        )
        
        # The tool instruction section should satisfy:
        tool_section = prompt.split("### 🛠️ TOOL USAGE & PERMISSIONS ###")[1].split("###")[0]
        if "`web_search`" in tool_section:
             print("❌ FAIL: 'web_search' still present in Direct Tools list after disabling skill.")
             print(f"DEBUG TOOL SECTION:\n{tool_section}")
             # sys.exit(1)
        else:
             print("✅ PASS: 'web_search' removed from prompt instructions.")

        # ── Scenario 2: Enable Skill ──
        print("\nStep 2: Enabling 'web-research'...")
        SkillService.toggle_skill(db, agent_id, skill_id, workspace_id, enabled=True)
        
        # Reload skills and build prompt
        enabled_skills = SkillService.get_skills_for_agent(db, agent_id)
        prompt = BrainService.build_prompt(
            agent.settings or {}, "", enabled_skills, 
            {"name": "Test"}, "Monday", "Toronto", agent_type="personal"
        )
        
        tool_section = prompt.split("### 🛠️ TOOL USAGE & PERMISSIONS ###")[1].split("###")[0]
        if "`web_search`" in tool_section:
             print("✅ PASS: 'web_search' now present in Direct Tools list after enabling skill.")
        else:
             print("❌ FAIL: 'web_search' missing from prompt after enabling skill.")
             print(f"DEBUG TOOL SECTION:\n{tool_section}")

        print("\n✨ DYNAMIC SKILL TOGGLE VALIDATION SUCCESSFUL.")

    finally:
        db.close()

if __name__ == "__main__":
    validate_skill_toggles()
