from typing import Optional
from sqlalchemy.orm import Session
from .agents.orchestrator import AgentOrchestrator

class AgentManager:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()

    async def chat(self, message: str, team_id: str, workspace_id: str, history: list = [], stream: bool = False, 
                   agent_id: str = None, agent_config: dict = None, communication_id: str = None, 
                   db: Optional[Session] = None) -> str:
        """Lightweight proxy to AgentOrchestrator."""
        return await self.orchestrator.chat(
            message=message,
            team_id=team_id,
            workspace_id=workspace_id,
            history=history,
            stream=stream,
            agent_id=agent_id,
            agent_config=agent_config,
            communication_id=communication_id,
            db=db
        )
