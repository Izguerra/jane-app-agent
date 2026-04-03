import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from agno.agent import Agent
from agno.models.openai import OpenAIChat as LLMModel
from backend.prompts import GATEKEEPER_INSTRUCTION
from backend.prompts.personal_assistant import PERSONAL_ASSISTANT_INSTRUCTION
from backend.models_db import Workspace
from backend.database import SessionLocal

class AgentFactory:
    @staticmethod
    def create_agent(settings: dict, workspace_id: str, team_id: str, tools: list = [], current_customer=None, 
                     customer_history_context: str = None, enabled_skills: list = [], personality_prompt: str = None, 
                     db: Optional[Session] = None) -> Agent:
        
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        p_business_name = settings.get("business_name", "The Business")
        p_services = settings.get("services", "General Inquiry")
        p_role = settings.get("name", "AI Assistant")
        agent_type = settings.get("agent_type", "business")
        
        # Select Base Instruction
        if agent_type == "personal":
            gatekeeper_instruction = PERSONAL_ASSISTANT_INSTRUCTION.format(
                owner_name=settings.get("owner_name", "User"),
                location=settings.get("personal_location", "Not specified"),
                timezone=settings.get("personal_timezone", "Not specified"),
                favorite_foods=settings.get("favorite_foods", "Not specified"),
                favorite_restaurants=settings.get("favorite_restaurants", "Not specified"),
                favorite_music=settings.get("favorite_music", "Not specified"),
                favorite_activities=settings.get("favorite_activities", "Not specified"),
                other_interests=settings.get("other_interests", "Not specified"),
                likes=settings.get("personal_likes", "Not specified"),
                dislikes=settings.get("personal_dislikes", "Not specified"),
                allowed_worker_list="- Full Access"
            )
        else:
            gatekeeper_instruction = GATEKEEPER_INSTRUCTION.format(
                business_name=p_business_name,
                services=p_services,
                role=p_role,
                allowed_worker_list="\n".join([f"- {w}" for w in settings.get("allowed_worker_types", [])])
            )

        instructions = [
            f"CURRENT DATE AND TIME: {current_datetime}.",
            f"AGENT SOUL:\n{settings.get('soul', '')}" if settings.get('soul') else "",
            f"BASE INSTRUCTIONS:\n{settings.get('prompt_template', '')}" if settings.get('prompt_template') else "",
            gatekeeper_instruction,
            f"PERSONALITY & TONE:\n{personality_prompt}" if personality_prompt else "",
            "Always be polite, professional, and empathetic.",
        ]

        if enabled_skills:
            skills_text = "\n".join([f"- {s.name} ({s.slug}): {s.instructions}" for s in enabled_skills])
            instructions.append(f"AGENT SKILLS & CAPABILITIES:\n{skills_text}")
        
        # Model Selection
        openai_api_key = os.getenv("OPENAI_API_KEY")
        model = LLMModel(id="gpt-4o-mini", api_key=openai_api_key, 
                         temperature=float(settings.get("creativity_level", 50)) / 100.0)

        return Agent(
            model=model,
            description="You are SupaAgent, an AI assistant.",
            instructions=instructions,
            tools=tools,
            markdown=True
        )
