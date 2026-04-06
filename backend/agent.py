from typing import Optional
from sqlalchemy.orm import Session
from .agents.orchestrator import AgentOrchestrator

class AgentManager:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()

    def _create_agent(self, settings: dict, workspace_id: str, team_id: str, tools: list = [], db: Optional[Session] = None, **kwargs):
        """Legacy proxy to AgentFactory.create_agent used by voice routers and tests."""
        from backend.agents.factory import AgentFactory
        return AgentFactory.create_agent(
            settings=settings,
            workspace_id=workspace_id,
            team_id=team_id,
            tools=tools,
            db=db,
            **kwargs
        )

    @staticmethod
    def _detect_context_needs(message: str) -> dict:
        """
        Fast heuristic to determine if a message needs specific tool contexts.
        Used for Clawdbot optimization (Fast-Path).
        """
        msg = message.lower()
        
        # Simple keywords for context detection
        needs = {
            "shopify": any(kw in msg for kw in ["order", "shipping", "track", "buy", "product"]),
            "calendar": any(kw in msg for kw in ["book", "appointment", "schedule", "meeting", "calendar"]),
            "crm": any(kw in msg for kw in ["customer", "lead", "contact", "history", "notes", "previous"]),
            "kb": any(kw in msg for kw in ["how", "what", "where", "can you", "services", "hours", "price"]),
            "phone": any(kw in msg for kw in ["call", "phone", "number"])
        }
        
        return needs

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
