import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Agent, Skill, AgentSkill
from backend.lib.id_service import IdService

def apply_patch():
    print("🚀 Running Agent Stability Patch...")
    db = SessionLocal()
    try:
        workspace_id = 'wrk_000V7dMzXJLzP5mYgdf7FzjA3J'
        target_agent_id = 'agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ'
        
        # 1. Force Activate Supa Agent
        agent = db.query(Agent).filter(Agent.id == target_agent_id).first()
        if agent:
            agent.is_active = True
            print(f"✅ Activated Agent: {agent.name} ({agent.id})")
        else:
            print(f"❌ Target Agent {target_agent_id} NOT FOUND")
            return

        # 2. Deactivate other agents in same workspace to prevent fallback confusion
        others = db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.id != target_agent_id
        ).all()
        for a in others:
            a.is_active = False
            print(f"💤 Deactivated Agent: {a.name} ({a.id})")

        # 3. Ensure Core Skills are enabled for Supa Agent
        # We include weather, maps, and general-utility (for time)
        essential_slugs = [
            "weather-worker", 
            "map-worker", 
            "general-utility", 
            "web-research", 
            "sms-messaging", 
            "email-worker"
        ]
        
        for slug in essential_slugs:
            skill = db.query(Skill).filter(Skill.slug == slug).first()
            if not skill:
                print(f"⚠️  Skill '{slug}' not found in DB catalog.")
                continue
                
            # Check if enabled
            askill = db.query(AgentSkill).filter(
                AgentSkill.agent_id == target_agent_id,
                AgentSkill.skill_id == skill.id
            ).first()
            
            if not askill:
                db.add(AgentSkill(
                    id=IdService.generate("askl"),
                    agent_id=target_agent_id,
                    skill_id=skill.id,
                    workspace_id=workspace_id,
                    enabled=True
                ))
                print(f"➕ Provisioned Skill: {slug}")
            else:
                askill.enabled = True
                askill.workspace_id = workspace_id # Ensure workspace_id is set
                print(f"✅ Verified Skill: {slug}")

        db.commit()
        print("\n✨ Database Patch Applied Successfully.")
        
    except Exception as e:
        print(f"❌ Patch Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    apply_patch()
