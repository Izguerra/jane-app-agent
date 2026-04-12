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
from backend.services.brain_service import BrainService

class AgentFactory:
    @staticmethod
    def create_agent(settings: dict, workspace_id: str, team_id: str, tools: list = [], 
                     current_customer=None, 
                     customer_history_context: str = None, enabled_skills: list = [], personality_prompt: str = None, 
                     db: Optional[Session] = None, current_datetime: str = None, **kwargs) -> Agent:
        
        if not current_datetime:
            import pytz
            toronto_tz = pytz.timezone("America/Toronto")
            current_datetime = datetime.now(toronto_tz).strftime("%A, %B %d, %Y at %I:%M %p")
            
        p_business_name = settings.get("business_name", "The Business")
        p_services = settings.get("services", "General Inquiry")
        p_role = settings.get("name", "AI Assistant")
        agent_type = settings.get("agent_type", "business")
        
        workspace_info = {
            "name": p_business_name,
            "phone": settings.get("phone", "N/A"),
            "services": p_services,
            "role": p_role
        }

        # Use the Unified Prompt Builder (One Brain)
        instructions = BrainService.build_prompt(
            settings=settings,
            personality_prompt=personality_prompt,
            enabled_skills=enabled_skills,
            workspace_info=workspace_info,
            current_datetime_str=current_datetime,
            client_location=settings.get("client_location"),
            agent_type=agent_type
        )
        
        # Model Selection
        openai_api_key = os.getenv("OPENAI_API_KEY")
        model_id = settings.get("model_id", "gpt-4o-mini") # Allow override
        model = LLMModel(id=model_id, api_key=openai_api_key, 
                         temperature=float(settings.get("creativity_level", 50)) / 100.0)

        return Agent(
            model=model,
            description=f"You are {p_role}, an AI assistant.",
            instructions=instructions,
            tools=tools,
            markdown=True,
            **kwargs
        )
