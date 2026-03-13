from typing import Optional
from sqlalchemy.orm import Session
from backend.agents.factory import AgentFactory

class AgentOrchestrator:
    @staticmethod
    async def chat(message: str, team_id: str, workspace_id: str, history: list = [], stream: bool = False, 
                   agent_id: str = None, agent_config: dict = None, communication_id: str = None, 
                   db: Optional[Session] = None) -> str:
        
        # Simplified for refactor
        # In reality, this would replicate the complex data fetching and tool assembly from agent.py
        settings = agent_config or {}
        agent = AgentFactory.create_agent(settings, workspace_id, team_id, db=db)
        
        if stream:
            return agent.arun(message, stream=True)
        else:
            res = await agent.arun(message)
            return res.content
