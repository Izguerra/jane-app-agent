from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models_db import Skill, AgentSkill
from backend.lib.id_service import IdService

class SkillService:
    @staticmethod
    def get_skills_catalog(db: Session, workspace_id: str) -> List[Skill]:
        """Get all available skills (system + custom for this workspace)"""
        return db.query(Skill).filter(
            (Skill.is_system == True) | (Skill.workspace_id == workspace_id)
        ).all()

    @staticmethod
    def get_skills_for_agent(db: Session, agent_id: str) -> List[Skill]:
        """Get enabled skills for a specific agent with full instructions"""
        return db.query(Skill).join(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.enabled == True
        ).all()

    @staticmethod
    def toggle_skill(db: Session, agent_id: str, skill_id: str, workspace_id: str, enabled: bool) -> AgentSkill:
        """Enable or disable a skill for an agent"""
        agent_skill = db.query(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == skill_id,
            AgentSkill.workspace_id == workspace_id
        ).first()

        if not agent_skill:
            agent_skill = AgentSkill(
                id=IdService.generate("askl"),
                agent_id=agent_id,
                skill_id=skill_id,
                workspace_id=workspace_id,
                enabled=enabled
            )
            db.add(agent_skill)
        else:
            agent_skill.enabled = enabled
        
        db.commit()
        db.refresh(agent_skill)
        return agent_skill

    @staticmethod
    def bulk_sync_skills(db: Session, agent_id: str, workspace_id: str, enabled_skill_ids: List[str]):
        """Syncs all skills for an agent, enabling those in the list and disabling the rest."""
        existing = db.query(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.workspace_id == workspace_id
        ).all()
        
        existing_map = {s.skill_id: s for s in existing}
        
        # Track which ones we process
        processed = set()
        
        for sid in enabled_skill_ids:
            processed.add(sid)
            if sid in existing_map:
                existing_map[sid].enabled = True
            else:
                db.add(AgentSkill(
                    id=IdService.generate("askl"),
                    agent_id=agent_id,
                    skill_id=sid,
                    workspace_id=workspace_id,
                    enabled=True
                ))
                
        for sid, skill_rec in existing_map.items():
            if sid not in processed:
                skill_rec.enabled = False
                
        db.commit()

    @staticmethod
    def create_custom_skill(db: Session, workspace_id: str, name: str, slug: str, category: str, instructions: str, allowed_tools: Optional[List[str]] = None) -> Skill:
        """Create a custom user-defined skill"""
        # Sanitize slug
        if not slug:
            slug = name.lower().replace(" ", "-")
        
        skill = Skill(
            id=IdService.generate("skll"),
            name=name,
            slug=slug,
            category=category,
            instructions=instructions,
            allowed_tools=allowed_tools,
            is_system=False,
            workspace_id=workspace_id
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill
