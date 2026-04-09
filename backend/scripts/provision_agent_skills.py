"""
Provision AgentSkill records for agents missing them.
Fixes the NOT NULL constraint on workspace_id that caused previous provisioning to fail.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import SessionLocal
from backend.models_db import Agent, Skill, AgentSkill
from backend.lib.id_service import IdService

def provision():
    db = SessionLocal()
    try:
        # Target: agents with 0 skills in the primary workspace
        workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
        agents = db.query(Agent).filter(Agent.workspace_id == workspace_id).all()

        for agent in agents:
            existing = db.query(AgentSkill).filter(AgentSkill.agent_id == agent.id).count()
            if existing > 0:
                print(f"SKIP: {agent.name} ({agent.id}) already has {existing} skills")
                continue

            # Enable the utility skills we added
            target_slugs = ["weather-worker", "map-worker", "flight-tracker", "general-utility",
                            "web-research", "advanced-browsing"]
            
            for slug in target_slugs:
                skill = db.query(Skill).filter(Skill.slug == slug).first()
                if skill:
                    db.add(AgentSkill(
                        id=IdService.generate("askl"),
                        agent_id=agent.id,
                        skill_id=skill.id,
                        workspace_id=workspace_id,  # ← THE FIX: NOT NULL column
                        enabled=True
                    ))
                    print(f"  ✅ Enabled '{slug}' for {agent.name}")
                else:
                    print(f"  ⚠️  Skill '{slug}' not found in DB — run seed_skills.py first")

        db.commit()
        print("\n✅ Provisioning complete.")

        # Verify
        for agent in agents:
            count = db.query(AgentSkill).filter(
                AgentSkill.agent_id == agent.id, AgentSkill.enabled == True
            ).count()
            print(f"  {agent.name}: {count} skills enabled")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    provision()
