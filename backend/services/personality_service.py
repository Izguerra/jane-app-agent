from typing import Optional
from sqlalchemy.orm import Session
from backend.models_db import AgentPersonality
from backend.lib.id_service import IdService

class PersonalityService:
    @staticmethod
    def get_personality(db: Session, agent_id: str) -> AgentPersonality:
        personality = db.query(AgentPersonality).filter(AgentPersonality.agent_id == agent_id).first()
        if not personality:
            # Return a "Standard Assistant" fallback instead of None
            return AgentPersonality(
                agent_id=agent_id,
                communication_style="Professional, warm, and highly efficient. You sound like a knowledgeable digital assistant.",
                core_values="Helpfulness, clarity, and proactive problem solving.",
                tone_guide="Clear and concise naturally-spoken English. Avoid robotic or overly formal phrasing.",
                brand_voice="A trusted, helpful advisor who gets things done."
            )
        return personality

    @staticmethod
    def save_personality(db: Session, agent_id: str, workspace_id: str, data: dict) -> AgentPersonality:
        personality = db.query(AgentPersonality).filter(AgentPersonality.agent_id == agent_id).first()
        
        if not personality:
            personality = AgentPersonality(
                id=IdService.generate("psnl"),
                agent_id=agent_id,
                workspace_id=workspace_id
            )
            db.add(personality)
        
        personality.communication_style = data.get("communication_style")
        personality.core_values = data.get("core_values")
        personality.tone_guide = data.get("tone_guide")
        personality.good_examples = data.get("good_examples")
        personality.bad_examples = data.get("bad_examples")
        personality.brand_voice = data.get("brand_voice")
        
        db.commit()
        db.refresh(personality)
        return personality

    @staticmethod
    def generate_personality_prompt(personality: AgentPersonality) -> str:
        """Construct the SOUL.md-style personality prompt section"""
        if not personality:
            return ""
            
        prompt = "\n## IDENTITY & PERSONALITY\n"
        if personality.communication_style:
            prompt += f"Communication Style: {personality.communication_style}\n"
        if personality.core_values:
            prompt += f"Core Values: {personality.core_values}\n"
        if personality.tone_guide:
            prompt += f"Tone & Voice Guide: {personality.tone_guide}\n"
        if personality.good_examples:
            prompt += f"\nGood Response Examples (Sound like this):\n{personality.good_examples}\n"
        if personality.bad_examples:
            prompt += f"\nBad Response Examples (DO NOT sound like this):\n{personality.bad_examples}\n"
            
        return prompt
