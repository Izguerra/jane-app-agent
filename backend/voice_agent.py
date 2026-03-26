import logging
import os
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe, JobContext, JobProcess, cli, WorkerOptions, llm
import livekit.plugins.silero as silero

# DNS BYPASS FIX
import socket
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "jane-clinic-app-tupihomh.livekit.cloud":
        # Hardcode successful resolution for known LiveKit IPs to bypass Mac DNS issues
        # Returned as list of tuples (family, type, proto, canonname, sockaddr)
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.180.66', port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.181.18', port))
        ]
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _patched_getaddrinfo

# Path Setup — explicit paths for LiveKit subprocess safety (multiprocessing.spawn)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

# Lazy import setup
def get_voice_deps():
    from backend.database import SessionLocal, generate_comm_id
    from backend.models_db import Communication, Agent as AgentModel, Customer, Workspace
    from backend.settings_store import get_settings
    from backend.services.voice_context_resolver import VoiceContextResolver
    from backend.services.voice_prompt_builder import VoicePromptBuilder
    from backend.services.voice_pipeline_service import VoicePipelineService
    from backend.services.voice_handlers import VoiceHandlers
    from backend.agent_tools import AgentTools
    from backend.services.skill_service import SkillService
    from backend.services.personality_service import PersonalityService
    from backend.services.mcp_loader_service import MCPLoaderService
    
    return {
        "SessionLocal": SessionLocal,
        "generate_comm_id": generate_comm_id,
        "Communication": Communication,
        "AgentModel": AgentModel,
        "Customer": Customer,
        "Workspace": Workspace,
        "get_settings": get_settings,
        "VoiceContextResolver": VoiceContextResolver,
        "VoicePromptBuilder": VoicePromptBuilder,
        "VoicePipelineService": VoicePipelineService,
        "VoiceHandlers": VoiceHandlers,
        "AgentTools": AgentTools,
        "SkillService": SkillService,
        "PersonalityService": PersonalityService,
        "MCPLoaderService": MCPLoaderService
    }

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("voice-agent")

_vad_model = None
def get_vad_model():
    global _vad_model
    if _vad_model is None:
        _vad_model = silero.VAD.load()
    return _vad_model

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = get_vad_model()

async def entrypoint(ctx: JobContext):
    # Setup process manager signals if it exists in the global scope
    if 'pm' in globals():
        globals()['pm'].setup_signals(asyncio.get_event_loop())
        
    try:
        logger.info(f"Entrypoint started for room {ctx.room.name}")
        start_time = datetime.now(timezone.utc)
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await ctx.wait_for_participant()
        await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})

        # Lazy load dependencies within the spawned process
        deps = get_voice_deps()
        workspace_id, agent_id, call_context, meta = await deps["VoiceContextResolver"].resolve_context(ctx, participant)
        if not workspace_id:
            logger.warning(f"Closing entrypoint for room {ctx.room.name} - Context could not be resolved.")
            return

        settings = deps["get_settings"](workspace_id)
        settings.update(meta)

        # 2. Database & Logging
        db = deps["SessionLocal"]()
        log_id = settings.get("log_id")
        customer_id = None
        workspace_info = {"name": "The Business", "phone": "N/A", "services": "General", "role": "Assistant"}

        try:
            # Correct logic: Use agent_id if provided by resolver, otherwise fallback to first in workspace
            if agent_id:
                agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].id == agent_id, deps["AgentModel"].workspace_id == workspace_id).first()
            else:
                agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].workspace_id == workspace_id).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: settings.update(agent_rec.settings)
                
                # CRITICAL: Ensure the explicit agent_id from room metadata takes precedence
                # over whatever settings.update() just merged (which might be the orchestrator agent)
                agent_id = meta.get("agent_id") or agent_id
                logger.info(f"Final resolved agent_id for execution: {agent_id}")
                
                # Inject allowed_worker_types directly from the model into settings
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types or []
                
                # RE-APPLY meta LAST to ensure UI temporary overrides (like agent_type and skills) take precedence
                if meta:
                    settings.update(meta)

                # Query Workspace directly — Agent model has no 'workspace' relationship
                ws = db.query(deps["Workspace"]).filter(deps["Workspace"].id == workspace_id).first()
                if ws:
                    workspace_info = {"name": ws.name, "phone": ws.phone, "services": settings.get("services"), "role": settings.get("role")}
                
            if not log_id:
                log_entry = deps["Communication"](
                    id=deps["generate_comm_id"](), type="call", direction="outbound" if call_context else "inbound",
                    status="ongoing", started_at=start_time, workspace_id=workspace_id, agent_id=agent_id
                )
                db.add(log_entry)
                db.commit()
                log_id = log_entry.id
                
            # 3. Build Prompt (Kept within the same DB session block)
            logger.info(f"Loading skills and personality for agent_id={agent_id}")
            skills = deps["SkillService"]().get_skills_for_agent(db, agent_id)
            personality = deps["PersonalityService"]().get_personality(db, agent_id)
            personality_prompt = deps["PersonalityService"]().generate_personality_prompt(personality)
        finally: db.close()

        prompt = deps["VoicePromptBuilder"].build_prompt(
            settings, personality_prompt, skills, workspace_info, 
            start_time.strftime("%A, %B %d, %Y at %I:%M %p"), settings.get("client_location")
        )

        # Inject cross-channel context memory (Layer 2)
        try:
            from backend.services.agent_context_service import AgentContextService
            # Use participant identity or phone number for customer resolution
            caller_id = participant.identity or settings.get("caller_phone") or settings.get("user_identifier")
            if caller_id:
                context_prompt = AgentContextService.build_context_prompt(
                    workspace_id=workspace_id, identifier=caller_id, channel="voice", limit=10, hours=72, agent_id=agent_id
                )
                if context_prompt:
                    prompt += f"\n\n{context_prompt}"
                    logger.info(f"Injected cross-channel context for caller: {caller_id}")
        except Exception as e:
            logger.warning(f"Context injection failed (non-fatal): {e}")

        # 4. Filtered Tools & Pipeline Setup
        voice_id = settings.get("voice_id", "alloy")
        
        # Standard tools first
        from backend.tools.worker_tools import WorkerTools
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = deps["AgentTools"](workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        all_tools = llm.find_function_tools(agent_tools)

        # Inject MCP Tools (Granular Permission Check)
        enabled_slugs = [s.slug for s in skills]
        
        # Include allowed_worker_types in enabled_slugs so they trigger MCP loading (e.g., lead-research -> Browser)
        allowed_workers = settings.get("allowed_worker_types") or []
        enabled_slugs = list(set(enabled_slugs + allowed_workers))
        
        if "skills" in settings and isinstance(settings["skills"], list):
            enabled_slugs = list(set(enabled_slugs + settings["skills"]))
            
        mcp_tools, mcp_instances, _ = await deps["MCPLoaderService"].load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools:
            logger.info(f"[Voice {agent_id}] Loaded {len(mcp_tools)} MCP tools. Total tools: {len(all_tools)}")
            all_tools.extend(mcp_tools)
        
        logger.info(f"Loading {len(all_tools)} tools for Voice Agent (Filtered by skills)")
        
        logger.info("Initializing AgentSession pipeline")
        agent = await deps["VoicePipelineService"].get_multimodal_agent(workspace_id, voice_id, prompt, all_tools)
        if agent:
            logger.info("Starting Multimodal Agent")
            await agent.start(ctx.room, participant)
        else:
            logger.info("Starting Standard AgentSession")
            from livekit.agents import TurnHandlingOptions
            from livekit.agents.voice import AgentSession, Agent as VoiceAgent
            logger.info("Initializing Standard AgentSession with Adaptive Interruption Handling...")
            session = AgentSession(
                vad=get_vad_model(), 
                stt=deps["VoicePipelineService"].get_stt(workspace_id),
                llm=deps["VoicePipelineService"].get_llm(workspace_id, settings),
                tts=deps["VoicePipelineService"].get_tts(workspace_id, voice_id, settings),
                tools=all_tools,
                turn_handling=TurnHandlingOptions(interruption={"mode": "adaptive"})
            )
            # Inject session back into agent_tools for filler logic
            agent_tools.session = session
            
            deps["VoiceHandlers"].register_session_events(session, ctx)
            await session.start(VoiceAgent(instructions=prompt), room=ctx.room)
            await asyncio.sleep(0.8)
            session.say(settings.get("welcome_message", "Hello! How can I help you?"))

        # 5. Wait & Cleanup
        shutdown_event = asyncio.Event()
        ctx.room.on("disconnected", lambda _: shutdown_event.set())
        await shutdown_event.wait()
        
        await deps["MCPLoaderService"].cleanup_mcp_servers(mcp_instances)
        await deps["VoiceHandlers"].capture_and_save_transcript(locals().get('session'), log_id, workspace_id, start_time)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN VOICE AGENT ENTRYPOINT: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise

from backend.utils.process_manager import ProcessManager

if __name__ == "__main__":
    # Load environment variables early for worker registration
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_project_root, "..", ".env"))

    pm = ProcessManager(name="voice-agent", pid_file=os.path.join(_project_root, "voice_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=os.getenv("AGENT_NAME", "supaagent-voice-v2.1")))
    finally:
        pm.cleanup()
