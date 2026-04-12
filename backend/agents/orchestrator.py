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

        ctx_db = db or SessionLocal()
        try:
            agent_rec = None
            if agent_id:
                agent_rec = ctx_db.query(AgentModel).filter(
                    AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id
                ).first()
            if not agent_rec:
                agent_rec = ctx_db.query(AgentModel).filter(
                    AgentModel.workspace_id == workspace_id,
                    AgentModel.is_active == True
                ).order_by(AgentModel.created_at.desc()).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings:
                    merged = dict(agent_rec.settings)
                    merged.update(settings)
                    settings = merged
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types or []
                settings["soul"] = agent_rec.soul
                settings["voice_id"] = agent_rec.voice_id
                settings["language"] = agent_rec.language
            
            skills = SkillService.get_skills_for_agent(ctx_db, agent_id)
            enabled_skill_slugs = [s.slug for s in skills]
            
            personality_prompt = None
            try:
                personality = PersonalityService().get_personality(ctx_db, agent_id)
                personality_prompt = PersonalityService().generate_personality_prompt(personality)
            except Exception as e:
                logger.warning(f"Personality load failed (non-fatal): {e}")
        finally:
            if not db:
                ctx_db.close()

        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(workspace_id=workspace_id, agent_id=agent_id, communication_id=communication_id, worker_tools=worker_tools)
        
        mcp_tools = []
        try:
            mcp_tools = MCPLoaderService.get_cached_mcp_tools(workspace_id, enabled_skill_slugs)
        except Exception as e:
            logger.warning(f"MCP loading failed: {e}")
        
        from livekit.agents import llm
        from backend.services.brain_service import BrainService
        
        lk_tools = llm.find_function_tools(agent_tools)
        all_lk_tools = lk_tools + mcp_tools
        allowed_tool_names = BrainService.get_allowed_tool_names(skills)
        
        def create_agno_wrapper(func_name, agent_tools_instance, tool_obj):
            actual_func = getattr(tool_obj, "_func", None)
            if not actual_func:
                if hasattr(tool_obj, "info") and hasattr(tool_obj, "execute"):
                    async def mcp_wrapper(*args, **kwargs):
                        return await tool_obj.execute(*args, **kwargs)
                    mcp_wrapper.__name__ = func_name
                    mcp_wrapper.__doc__ = tool_obj.info.description
                    return mcp_wrapper
                return None
                
            raw_func = getattr(actual_func, "__wrapped__", actual_func)
            sig = inspect.signature(raw_func)
            new_params = [p for p in sig.parameters.values() if p.name != 'self']
            new_sig = sig.replace(parameters=new_params)
            
            async def wrapper(*args, **kwargs):
                if inspect.ismethod(actual_func):
                    return await actual_func(*args, **kwargs)
                return await raw_func(agent_tools_instance, *args, **kwargs)
                
            wrapper.__name__ = func_name
            wrapper.__doc__ = raw_func.__doc__
            wrapper.__signature__ = new_sig
            if hasattr(raw_func, "__annotations__"):
                wrapper.__annotations__ = {k: v for k, v in raw_func.__annotations__.items() if k != "self"}
            return wrapper
        
        tools = []
        for tool in all_lk_tools:
            tool_name = getattr(tool.info, "name", None) if hasattr(tool, "info") else getattr(tool, "name", None)
            is_mcp = tool in mcp_tools
            if is_mcp or (tool_name in allowed_tool_names):
                wrapped_tool = create_agno_wrapper(tool_name, agent_tools, tool)
                if wrapped_tool: tools.append(wrapped_tool)

        from agno.team import Team
        ref_tz_name = settings.get("client_timezone", "America/Toronto")
        ref_tz = pytz.timezone(ref_tz_name)
        ref_time_str = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        
        expert_agent = AgentFactory.create_agent(
            dict(settings, model_id="gpt-4o"), workspace_id, team_id, tools=tools, db=db,
            enabled_skills=skills, current_datetime=ref_time_str, enable_agentic_state=True
        )
        expert_agent.name = "Expert"
        
        frontline_settings = dict(settings, model_id="gpt-4o-mini")
        jane_agent = AgentFactory.create_agent(
            frontline_settings, workspace_id, team_id, tools=[], db=db,
            enabled_skills=skills, personality_prompt=personality_prompt,
            current_datetime=ref_time_str, enable_agentic_state=True
        )
        jane_agent.name = settings.get("name", "Jane")

        agent = Team(members=[jane_agent, expert_agent], show_members_responses=True, add_member_tools_to_context=True, add_team_history_to_members=True)
        
        from agno.models.message import Message
        from backend.services.agent_context_service import AgentContextService
        messages = []
        for msg in history:
            role = "assistant" if (msg.role if hasattr(msg, "role") else msg.get("role")) == "ai" else "user"
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            if content: messages.append(Message(role=role, content=content))
        messages.append(Message(role="user", content=message))
        
        if stream: return agent.arun(messages, stream=True)
        else:
            res = await agent.arun(messages)
            return res.content
