from typing import Optional
import logging
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
            if not agent_rec:
                agent_rec = ctx_db.query(AgentModel).filter(
                    AgentModel.workspace_id == workspace_id
                ).first()
            
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
        
        # ── 5. Load MCP Tools (with proper lifecycle tracking) ──
        mcp_tools = []
        mcp_instances = []
        try:
            mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_skill_slugs)
        except Exception as e:
            logger.warning(f"MCP loading failed (non-fatal, continuing without MCP tools): {e}")
        
        # ── 6. Extract tools for Agno (Robust Extraction) ──
        from livekit.agents import llm
        
        # Get all standard tools via LiveKit's discovery
        lk_tools = llm.find_function_tools(agent_tools)
        
        # Start with MCP tools (which are already lk.FunctionTool wrappers)
        all_lk_tools = lk_tools + mcp_tools
        
        tools = []
        for tool in all_lk_tools:
            tool_name = getattr(tool, "name", None)
            actual_method = getattr(tool, "_func", None)
            desc = getattr(tool, "description", "")
            
            # EXPLICIT AGNO MAPPINGS FOR PROBLEMATIC MIXIN TOOLS
            print(f"DEBUG: Checking tool_name: {tool_name}")
            
            if tool_name in ("send_sms_notification", "send-sms-notification", "send_sms_notification_communication_mixin"):
                async def send_sms_notification(phone_number: str, message: str) -> str:
                    from backend.services.sms_service import send_sms
                    success, error = send_sms(phone_number, message, agent_tools.workspace_id)
                    return "SMS sent successfully." if success else f"Failed to send SMS: {error}"
                send_sms_notification.__doc__ = desc
                tools.append(send_sms_notification)
                print("DEBUG: Appended pure SMS tool!")
                continue
                
            elif tool_name in ("send_email_notification", "send-email-notification", "send_email_notification_communication_mixin"):
                async def send_email_notification(email_address: str, subject: str, message: str) -> str:
                    from backend.services.email_service import EmailService
                    success, error = EmailService().send_email(to_email=email_address, subject=subject, html_content=f"<p>{message}</p>", workspace_id=agent_tools.workspace_id)
                    return "Email sent successfully." if success else f"Failed to send email: {error}"
                send_email_notification.__doc__ = desc
                tools.append(send_email_notification)
                print("DEBUG: Appended pure Email tool!")
                continue
            
            # Fallback to the raw inner function (e.g., for MCP closures and others)
            elif actual_method:
                tools.append(actual_method)
                logger.debug(f"Added standalone tool to Chatbot: {tool_name or 'unknown'}")
        # ── 7. Create agent with full context ──
        agent = AgentFactory.create_agent(
            settings, workspace_id, team_id, tools=tools, db=db,
            enabled_skills=skills, personality_prompt=personality_prompt
        )
        # Enable observability for tool calls in chat mode
        agent.show_tool_calls = True
        
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
            content = msg.content if hasattr(msg, "content") else msg.get("content", "") if isinstance(msg, dict) else ""
            if content:
                messages.append(Message(role=role, content=content))
        
        messages.append(Message(role="user", content=message))
        
        # ── 9. Run agent and ensure MCP cleanup ──
        try:
            if stream:
                return agent.arun(messages, stream=True)
            else:
                res = await agent.arun(messages)
                return res.content
        finally:
            # Cleanup MCP connections to prevent async lifecycle errors
            if mcp_instances:
                try:
                    await MCPLoaderService.cleanup_mcp_servers(mcp_instances)
                except Exception as e:
                    logger.warning(f"MCP cleanup failed (non-fatal): {e}")

