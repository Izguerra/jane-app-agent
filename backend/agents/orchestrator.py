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
        from backend.services.skill_service import SkillService
        from backend.services.mcp_loader_service import MCPLoaderService
        from backend.database import SessionLocal

        # 1. Fetch enabled skills for the agent
        ctx_db = db or SessionLocal()
        try:
            skills = SkillService.get_skills_for_agent(ctx_db, agent_id)
            enabled_skill_slugs = [s.slug for s in skills]
        finally:
            if not db: ctx_db.close()

        # 2. Setup standard tools
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(
            workspace_id=workspace_id, 
            agent_id=agent_id, 
            communication_id=communication_id, 
            worker_tools=worker_tools
        )
        
        # 3. Load Authorized MCP Tools
        mcp_tools, _ = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_skill_slugs)
        
        # Assemble all potential tool members
        all_potential_tools = []
        import inspect
        all_potential_tools.extend([m for _, m in inspect.getmembers(agent_tools)])
        all_potential_tools.extend(mcp_tools)

        # 4. Extract and process tools for Agno
        tools = []
        for member in all_potential_tools:
            name = getattr(member, "name", getattr(member, "__name__", "unknown_tool"))
            # Check if it's a LiveKit FunctionTool wrapper
            if type(member).__name__ == "FunctionTool":
                # Extract the pure python function for Agno
                actual_method = getattr(member, "__wrapped__", getattr(member, "_func", None))
                if actual_method and not name.startswith("_"):
                    import types
                    # Agno needs methods to be bound to their instances if they use self
                    if hasattr(member, "_func") and inspect.ismethod(member._func):
                        tools.append(member._func)
                    else:
                        tools.append(actual_method)
            # Fallback for manually decorated or raw methods from AgentTools
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
