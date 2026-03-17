from typing import Optional
from sqlalchemy.orm import Session
from backend.agents.factory import AgentFactory

class AgentOrchestrator:
    @staticmethod
    async def chat(message: str, team_id: str, workspace_id: str, history: list = [], stream: bool = False, 
                   agent_id: str = None, agent_config: dict = None, communication_id: str = None, 
                   db: Optional[Session] = None) -> str:
        
        settings = agent_config or {}

        # Assemble Tools
        from backend.agent_tools import AgentTools
        from backend.tools.worker_tools import WorkerTools

        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(
            workspace_id=workspace_id, 
            agent_id=agent_id, 
            communication_id=communication_id, 
            worker_tools=worker_tools
        )
        
        # Extract tool methods — only include methods decorated with @llm.function_tool
        import inspect
        tools = []
        for name, member in inspect.getmembers(agent_tools):
            # Check if it's a LiveKit FunctionTool wrapper
            if type(member).__name__ == "FunctionTool":
                # Extract the pure python function for Agno
                actual_method = getattr(member, "__wrapped__", getattr(member, "_func", None))
                if actual_method and not name.startswith("_"):
                    import types
                    bound_method = types.MethodType(actual_method, agent_tools)
                    tools.append(bound_method)
            # Fallback for manually decorated or raw methods
            elif inspect.ismethod(member) and hasattr(member, "__llm_function__") and not name.startswith("_"):
                tools.append(member)

        agent = AgentFactory.create_agent(settings, workspace_id, team_id, tools=tools, db=db)
        
        # Build enriched conversation context with cross-channel memory
        from agno.models.message import Message
        from backend.services.agent_context_service import AgentContextService
        
        messages = []
        
        # Enrich with cross-channel context if we have a communication_id
        try:
            if communication_id:
                # Get the user_identifier from the communication record
                from backend.database import SessionLocal
                from backend.models_db import Communication
                ctx_db = SessionLocal()
                try:
                    comm = ctx_db.query(Communication).filter(Communication.id == communication_id).first()
                    if comm and comm.user_identifier:
                        enriched_history = AgentContextService.enrich_history(
                            workspace_id=workspace_id,
                            identifier=comm.user_identifier,
                            current_history=history,
                            communication_id=communication_id,
                            channel=comm.channel
                        )
                        history = enriched_history
                finally:
                    ctx_db.close()
        except Exception as e:
            import logging
            logging.getLogger("orchestrator").warning(f"Context enrichment failed (non-fatal): {e}")

        # Convert history items to Agno Message objects
        for msg in history:
            role = msg.role if hasattr(msg, "role") else msg.get("role", "user") if isinstance(msg, dict) else "user"
            content = msg.content if hasattr(msg, "content") else msg.get("content", "") if isinstance(msg, dict) else ""
            if content:
                messages.append(Message(role=role, content=content))
        
        # Add the current user message
        messages.append(Message(role="user", content=message))
        
        if stream:
            return agent.arun(messages, stream=True)
        else:
            res = await agent.arun(messages)
            return res.content
