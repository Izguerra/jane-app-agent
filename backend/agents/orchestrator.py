from typing import Optional, List, Dict, Any, Union
import logging
from datetime import datetime
import json
import pytz
import inspect
from sqlalchemy.orm import Session
from backend.agents.factory import AgentFactory

logger = logging.getLogger("orchestrator")

class AgentOrchestrator:
    @staticmethod
    async def chat(message: str, team_id: str, workspace_id: str, history: list = [], stream: bool = False, 
                   agent_id: str = None, agent_config: dict = None, communication_id: str = None, 
                   db: Optional[Session] = None) -> str:
        
        settings = agent_config or {}

        from backend.agent_tools import AgentTools
        from backend.tools.worker_tools import WorkerTools
        from backend.services.skill_service import SkillService
        from backend.services.mcp_loader_service import MCPLoaderService
        from backend.services.personality_service import PersonalityService
        from backend.database import SessionLocal
        from backend.models_db import Agent as AgentModel

        # ── 1. Load Agent record from DB (matching voice/avatar agent pattern) ──
        ctx_db = db or SessionLocal()
        try:
            agent_rec = None
            if agent_id:
                agent_rec = ctx_db.query(AgentModel).filter(
                    AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id
                ).first()
                if agent_rec:
                    logger.info(f"Chatbot initialized with TARGET agent: {agent_rec.name} ({agent_rec.id})")
                else:
                    logger.warning(f"Requested agent_id '{agent_id}' not found in workspace '{workspace_id}'")

            if not agent_rec:
                # Fallback to the latest active agent in the workspace
                agent_rec = ctx_db.query(AgentModel).filter(
                    AgentModel.workspace_id == workspace_id,
                    AgentModel.is_active == True
                ).order_by(AgentModel.created_at.desc()).first()
                if agent_rec:
                    logger.info(f"Chatbot fallback resolved to ACTIVE agent: {agent_rec.name} ({agent_rec.id})")
                else:
                    logger.error(f"❌ No active agents found in workspace {workspace_id}")
            
            if agent_rec:
                agent_id = agent_rec.id
                # Merge agent's persisted settings into the runtime settings
                if agent_rec.settings:
                    # DB settings are the base; agent_config from frontend overrides
                    merged = dict(agent_rec.settings)
                    merged.update(settings)
                    settings = merged
                # Inject top-level columns (matching voice/avatar agent pattern)
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types or []
                settings["soul"] = agent_rec.soul
                settings["voice_id"] = agent_rec.voice_id
                settings["language"] = agent_rec.language
            
            # ── 2. Load Skills ──
            skills = SkillService.get_skills_for_agent(ctx_db, agent_id)
            enabled_skill_slugs = [s.slug for s in skills]
            
            # ── 3. Load Personality ──
            personality_prompt = None
            try:
                personality = PersonalityService().get_personality(ctx_db, agent_id)
                personality_prompt = PersonalityService().generate_personality_prompt(personality)
            except Exception as e:
                logger.warning(f"Personality load failed (non-fatal): {e}")
        finally:
            if not db:
                ctx_db.close()

        # ── 4. Setup tools ──
        worker_tools = WorkerTools(
            workspace_id=workspace_id, 
            allowed_worker_types=settings.get("allowed_worker_types", [])
        )
        agent_tools = AgentTools(
            workspace_id=workspace_id, 
            agent_id=agent_id, 
            communication_id=communication_id, 
            worker_tools=worker_tools
        )
        
        # ── 5. Load MCP Tools (LAZY LOADING for Chat Mode) ──
        mcp_tools = []
        try:
            # We use cached definitions to avoid SSE handshake latency (9s -> <1s)
            mcp_tools = MCPLoaderService.get_cached_mcp_tools(workspace_id, enabled_skill_slugs)
            logger.info(f"Chatbot Tool Discovery: Found {len(mcp_tools)} cached MCP tools.")
        except Exception as e:
            logger.warning(f"MCP loading failed (non-fatal, continuing without MCP tools): {e}")
        
        # ── 6. Extract tools for Agno (Robust Extraction) ──
        from livekit.agents import llm
        import inspect
        from backend.services.brain_service import BrainService
        
        # Get all standard tools via LiveKit's discovery
        lk_tools = llm.find_function_tools(agent_tools)
        
        # Start with MCP tools
        all_lk_tools = lk_tools + mcp_tools
        allowed_tool_names = BrainService.get_allowed_tool_names(skills)
        
        def create_agno_wrapper(func_name, agent_tools_instance, tool_obj):
            """
            Creates a clean Python function for Agno/Pydantic.
            Handles both standard AgentTools (requiring 'self' binding) and
            external tools (like MCP) which are self-contained.
            """
            # Extract the underlying execution function
            # Standard tools have '_func', MCP tools might be callable or have another execution path
            actual_func = getattr(tool_obj, "_func", None)
            
            if not actual_func:
                # If no _func, this is likely an MCP tool or a custom wrapper.
                # We return the tool's own function info if it exists
                if hasattr(tool_obj, "info") and hasattr(tool_obj, "execute"):
                    async def mcp_wrapper(*args, **kwargs):
                        try:
                            # MCP tools don't need 'self' from AgentTools
                            return await tool_obj.execute(*args, **kwargs)
                        except Exception as e:
                            logger.error(f"MCP Tool '{func_name}' failed: {e}")
                            raise
                    
                    mcp_wrapper.__name__ = func_name
                    mcp_wrapper.__doc__ = tool_obj.info.description
                    return mcp_wrapper
                return None
                
            # ── Standard Tool Logic (with 'self' binding) ──
            # Drill down to the raw original function avoiding Pydantic decorators
            raw_func = getattr(actual_func, "__wrapped__", actual_func)
            
            sig = inspect.signature(raw_func)
            new_params = [p for p in sig.parameters.values() if p.name != 'self']
            new_sig = sig.replace(parameters=new_params)
            
            async def wrapper(*args, **kwargs):
                try:
                    # IMPROVED BINDING LOGIC:
                    # If actual_func is already bound to an instance (e.g., from llm.find_function_tools(agent_tools)),
                    # we do NOT pass the instance again as it's already contextualized.
                    if inspect.ismethod(actual_func):
                        return await actual_func(*args, **kwargs)
                    
                    # Otherwise, safely pass the agent_tools instance as the first 'self' argument
                    return await raw_func(agent_tools_instance, *args, **kwargs)
                except Exception as e:
                    logger.error(f"System Tool '{func_name}' failed: {e}")
                    raise
                
            wrapper.__name__ = func_name
            wrapper.__qualname__ = func_name
            wrapper.__doc__ = raw_func.__doc__ or getattr(tool_obj, "description", "")
            wrapper.__signature__ = new_sig
            
            # Ensure type hints from the original function are preserved
            if hasattr(raw_func, "__annotations__"):
                wrapper.__annotations__ = {k: v for k, v in raw_func.__annotations__.items() if k != "self"}
            
            # CRITICAL: Agno uses get_type_hints which looks at __globals__
            # We ensure the wrapper shares globals with this module which now has Any/List/etc.
            return wrapper
        
        tools = []
        logger.info(f"Chatbot Tool Discovery: Initializing capabilities for agent '{agent_id}'...")
        
        # ── 6. Tool Filtering & Wrapping (Agno Compatibility) ──
        for tool in all_lk_tools:
            tool_name = getattr(tool.info, "name", None) if hasattr(tool, "info") else getattr(tool, "name", None)
            if not tool_name:
                continue

            # Identify source: Tools from AgentTools have _func, MCP tools are wrapped differently
            is_mcp = tool in mcp_tools
            
            # ACCESS CONTROL: 
            # - MCP tools are already filtered by server-level skill slugs in MCPLoaderService
            # - Standard tools are filtered by explicit method whitelist
            is_allowed = is_mcp or (tool_name in allowed_tool_names)
            
            if is_allowed:
                wrapped_tool = create_agno_wrapper(tool_name, agent_tools, tool)
                if wrapped_tool:
                    tools.append(wrapped_tool)
                    source_label = "MCP" if is_mcp else "SYSTEM"
                    logger.info(f"✅ EXPOSED [{source_label}] tool to Chatbot: {tool_name}")
                else:
                    # Final fallback: expose the raw function if everything else fails
                    actual_method = getattr(tool, "_func", None)
                    if actual_method:
                        tools.append(actual_method)
                        logger.info(f"✅ EXPOSED tool (fallback) to Chatbot: {tool_name}")
            else:
                logger.debug(f"🚫 BLOCKED tool from Chatbot (Not in skills): {tool_name}")

        # ── 7. Create 2-Tier Agent Team (Leader/Member Architecture) ──
        from agno.team import Team
        
        ref_tz_name = settings.get("client_timezone", "America/Toronto")
        ref_tz = pytz.timezone(ref_tz_name)
        ref_time_str = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        logger.info(f"Chatbot Ref Time ({ref_tz_name}): {ref_time_str}")
        
        # Expert Agent (Member): High performance, handles all specialized tools
        expert_settings = dict(settings)
        expert_settings["model_id"] = "gpt-4o"
        expert_agent = AgentFactory.create_agent(
            expert_settings, workspace_id, team_id, tools=tools, db=db,
            enabled_skills=skills, personality_prompt=None, # Pure tool executor
            current_datetime=ref_time_str,
            enable_agentic_state=True
        )
        expert_agent.name = "Expert"
        expert_agent.description = "You are a technical specialist responsible for executing tools and providing raw data to the primary assistant."
        
        # Jane (Leader): Fast conversational agent. Delegator.
        frontline_settings = dict(settings)
        frontline_settings["model_id"] = "gpt-4o-mini"
        
        # Inject delegation instructions into the personality/base prompt
        # Explicitly mention SMS/Email/Notifications skills to ensure she delegates them
        delegation_instr = (
            "\n\n### 🚨 CRITICAL DELEGATION RULES ###\n"
            "If the user asks for ANY of the following, you MUST DELEGATE to your 'Expert' team member:\n"
            "- SENDING SMS or EMAIL notifications\n"
            "- Running background tasks or workers\n"
            "- Weather, Knowledge Base Search, or Flight Status\n"
            "- Technical lookups or CRM updates\n"
            "Do NOT try to simulate these technical responses. Hand them off to the Expert immediately."
        )
        if personality_prompt:
            personality_prompt += delegation_instr
        else:
            personality_prompt = delegation_instr

        jane_agent = AgentFactory.create_agent(
            frontline_settings, workspace_id, team_id, tools=[], # Jane has NO tools herself
            db=db,
            enabled_skills=skills, personality_prompt=personality_prompt,
            current_datetime=ref_time_str,
            enable_agentic_state=True
        )
        jane_agent.name = settings.get("name", "Jane")

        # Wrap in a Team for proper delegation
        agent = Team(
            members=[jane_agent, expert_agent],
            show_members_responses=True,
            add_member_tools_to_context=True,
            add_team_history_to_members=True
        )
        
        logger.info(f"Chatbot 2-Tier Team Initialized. Members: {[jane_agent.name, expert_agent.name]} (Lead: {jane_agent.name}).")
        
        # ── 8. Build conversation context with cross-channel memory ──
        from agno.models.message import Message
        from backend.services.agent_context_service import AgentContextService
        
        messages = []
        
        try:
            if communication_id:
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
            logger.warning(f"Context enrichment failed (non-fatal): {e}")

        for msg in history:
            role = msg.role if hasattr(msg, "role") else msg.get("role", "user") if isinstance(msg, dict) else "user"
            # Normalize role for Agno/OpenAI
            if role == "ai":
                role = "assistant"
            
            content = msg.content if hasattr(msg, "content") else msg.get("content", "") if isinstance(msg, dict) else ""
            if content:
                messages.append(Message(role=role, content=content))
        
        messages.append(Message(role="user", content=message))
        
        # ── 9. Run agent ──
        if stream:
            return agent.arun(messages, stream=True)
        else:
            res = await agent.arun(messages)
            return res.content

