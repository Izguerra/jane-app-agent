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

    def _create_agent(self, settings: dict, workspace_id: str, team_id: str, tools: list = [], db: Optional[Session] = None):
        """Internal helper for prompt enrichment used by voice/avatar routers."""
        from .agents.factory import AgentFactory
        return AgentFactory.create_agent(settings, workspace_id, team_id, tools=tools, db=db)

    def create_agent(self, *args, **kwargs):
        """Alias for _create_agent."""
        return self._create_agent(*args, **kwargs)
