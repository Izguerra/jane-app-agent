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
        # 0. Quick context detection (Clawdbot Fast-Path)
        from backend.agent import AgentManager
        needs = AgentManager._detect_context_needs(message)
        has_serious_intent = any(needs.values())
        
        ctx_db = db or SessionLocal()
        
        # Parallel fetch settings and skills if serious
        import asyncio
        from backend.settings_store import get_settings
        from backend.services.skill_service import SkillService
        
        async def fetch_data():
            if has_serious_intent:
                # Fetch settings and skills in parallel
                # Note: get_settings and get_skills_for_agent are sync, wrap in threads
                settings_task = asyncio.to_thread(get_settings, workspace_id)
                skills_task = asyncio.to_thread(SkillService.get_skills_for_agent, ctx_db, agent_id)
                return await asyncio.gather(settings_task, skills_task)
            else:
                # Fast-Path: Just fetch settings (likely cached)
                return await asyncio.to_thread(get_settings, workspace_id), []

        db_settings, skills = await fetch_data()
        settings.update(db_settings)
        enabled_skill_slugs = [s.slug for s in skills]
        
        if settings.get("skills") and isinstance(settings["skills"], list):
            enabled_skill_slugs = list(set(enabled_skill_slugs + settings["skills"]))
        
        # Merge agent-specific overrides from DB record if provided
        if agent_id and has_serious_intent:
            try:
                from backend.models_db import Agent
                agent_rec = ctx_db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first()
                if agent_rec:
                    base_fields = ["name", "voice_id", "language", "prompt_template", "welcome_message"]
                    for field in base_fields:
                        val = getattr(agent_rec, field)
                        if val is not None: settings[field] = val
                    if agent_rec.settings: settings.update(agent_rec.settings)
                    settings["allowed_worker_types"] = agent_rec.allowed_worker_types
            except Exception as e:
                import logging
                logging.getLogger("orchestrator").error(f"Failed to load agent overrides: {e}")
            finally:
                if not db: ctx_db.close()

        # 2. Setup standard tools (Only if needed)
        tools = []
        agno_toolkits = []

        if has_serious_intent:
            worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
            agent_tools = AgentTools(
                workspace_id=workspace_id, 
                agent_id=agent_id, 
                communication_id=communication_id, 
                worker_tools=worker_tools
            )
            
            # 3. Load Authorized MCP Tools
            mcp_tools, _, agno_toolkits = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_skill_slugs)
            
            # 4. Extract and process tools for Agno
            import inspect
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
        
        # Enrich with cross-channel context ONLY for serious inquiries
        try:
            if communication_id and has_serious_intent:
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
