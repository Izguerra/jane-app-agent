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
        
        ctx_db = db or SessionLocal()

        # 0. Load Full Agent Settings from DB
        try:
            from backend.settings_store import get_settings
            db_settings = get_settings(workspace_id).copy()
            
            if agent_id:
                from backend.models_db import Agent
                agent_rec = ctx_db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first()
                if agent_rec:
                    base_fields = ["name", "voice_id", "language", "prompt_template", "welcome_message"]
                    for field in base_fields:
                        val = getattr(agent_rec, field)
                        if val is not None: db_settings[field] = val
                    if agent_rec.settings: db_settings.update(agent_rec.settings)
                    # Pass the worker allowance string to Prompt Builder
                    db_settings["allowed_worker_types"] = agent_rec.allowed_worker_types
            
            # Re-apply UI config on top
            db_settings.update(settings)
            settings = db_settings
        except Exception as e:
            import logging
            logging.getLogger("orchestrator").error(f"Failed to load agent settings: {e}")

        # 1. Fetch enabled skills for the agent
        try:
            skills = SkillService.get_skills_for_agent(ctx_db, agent_id)
            enabled_skill_slugs = [s.slug for s in skills]
            if settings.get("skills") and isinstance(settings["skills"], list):
                enabled_skill_slugs = list(set(enabled_skill_slugs + settings["skills"]))
        finally:
            if not db: ctx_db.close()

        # 2. Setup standard tools
        allowed_workers = settings.get("allowed_worker_types")
        if isinstance(allowed_workers, str):
            allowed_workers = [w.strip() for w in allowed_workers.split(",") if w.strip()]
        elif not isinstance(allowed_workers, list):
            allowed_workers = []
            
        import logging
        orchestrator_logger = logging.getLogger("orchestrator")
        orchestrator_logger.debug(f"Assembling tools for agent. Allowed workers: {allowed_workers}")

        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=allowed_workers)
        agent_tools = AgentTools(
            workspace_id=workspace_id, 
            agent_id=agent_id, 
            communication_id=communication_id, 
            worker_tools=worker_tools
        )
        
        # 3. Load Authorized MCP Tools
        mcp_tools, _, agno_toolkits = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_skill_slugs)
        
        # Assemble all potential tool members
        all_potential_tools = []
        import inspect
        all_potential_tools.extend([m for _, m in inspect.getmembers(agent_tools)])
        
        # 4. Extract and process tools for Agno
        tools = []
        # Add all methods from AgentTools
        for name, member in inspect.getmembers(agent_tools):
            if name.startswith("_"):
                continue
                
            # If it's a LiveKit FunctionTool (e.g. from @llm.function_tool)
            if hasattr(member, "_func"):
                raw_func = member._func
                # Bind the raw function to the agent_tools instance so Agno passes 'self'
                if hasattr(raw_func, "__get__"):
                    tools.append(raw_func.__get__(agent_tools))
                else:
                    tools.append(raw_func)
            
            # Standard Python methods
            elif inspect.ismethod(member):
                # Unwrap if it's got a __wrapped__ attribute (e.g. standard decorators)
                actual_method = getattr(member, "__wrapped__", member)
                if hasattr(actual_method, "__get__") and actual_method is not member:
                    tools.append(actual_method.__get__(agent_tools))
                else:
                    tools.append(member)
            
            # Fallback for manually decorated or specifically marked tools
            elif hasattr(member, "__llm_function__"):
                tools.append(member)

        # Add Agno MCP Toolkits directly! Agno automatically unpacks Toolkits.
        tools.extend(agno_toolkits)
        
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
                            channel=comm.channel,
                            agent_id=agent_id
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
