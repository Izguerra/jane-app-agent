# MINIMAL top-level imports and environment setup for spawn/forkserver safety
import logging
import os
import asyncio
import sys
from datetime import datetime, timezone

# Project root for relative pathing (global for spawn safety)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def initialize_agent_env():
    """
    Initializes the agent environment, ensuring paths and patches are applied.
    Safe to call in both main and spawned subprocesses.
    """
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    
    # Load environment variables early for child processes
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

    # Apply critical network patches (DNS bypass for macOS)
    try:
        from backend.utils.network_patch import apply_network_patches
        apply_network_patches()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Network patch failed to load: {e}")

# IMPORTANT: Call this at top-level so spawned children inherit the project root in sys.path
initialize_agent_env()

def get_avatar_deps():
    from livekit.rtc import ConnectionState
    from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
    
    from backend.avatar.config import resolve_settings, get_llm, get_tts
    from backend.avatar.prompts import get_avatar_prompt
    from backend.avatar.providers import initialize_avatar
    from backend.avatar.tracking import start_communication_log, finalize_communication_log
    from backend.services.voice_handlers import VoiceHandlers
    from backend.database import SessionLocal
    from backend.models_db import Agent as AgentModel, Workspace, Communication
    from backend.agent_tools import AgentTools
    from backend.services.mcp_loader_service import MCPLoaderService
    from backend.services.skill_service import SkillService
    from backend.services.voice_context_resolver import VoiceContextResolver
    from backend.services.voice_pipeline_service import VoicePipelineService
    
    return {
        "ConnectionState": ConnectionState,
        "AutoSubscribe": AutoSubscribe,
        "llm": llm,
        "resolve_settings": resolve_settings,
        "get_llm": get_llm,
        "get_tts": get_tts,
        "get_avatar_prompt": get_avatar_prompt,
        "initialize_avatar": initialize_avatar,
        "start_communication_log": start_communication_log,
        "finalize_communication_log": finalize_communication_log,
        "VoiceHandlers": VoiceHandlers,
        "SessionLocal": SessionLocal,
        "AgentModel": AgentModel,
        "Workspace": Workspace,
        "Communication": Communication,
        "AgentTools": AgentTools,
        "MCPLoaderService": MCPLoaderService,
        "SkillService": SkillService,
        "VoiceContextResolver": VoiceContextResolver,
        "VoicePipelineService": VoicePipelineService
    }

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-agent")

def prewarm(proc):
    initialize_agent_env()
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx):
    # Ensure environment is initialized in the entrypoint process
    initialize_agent_env()
    
    # Setup process manager signals if it exists in global scope
    if 'pm' in globals():
        globals()['pm'].setup_signals(asyncio.get_event_loop())

    agent = None
    mcp_instances = []
    log_id = None
    workspace_id = None
    start_time = datetime.now(timezone.utc)
    
    try:
        logger.info(f"🚀 [AVATAR {os.getpid()}] Entrypoint started for room {ctx.room.name}")
        
        # 1. CONNECTION
        from livekit.rtc import ConnectionState
        from livekit.agents import AutoSubscribe
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
            logger.info("✅ Agent connected to room")
        
        # Now we can safely set attributes on the local participant
        await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})
        
        logger.info("Waiting for participant to join...")
        participant = await ctx.wait_for_participant()
        
        # Lazy load dependencies within the spawned process
        deps = get_avatar_deps()
        
        # Resolve Settings & Agent Identity
        workspace_id, agent_id, call_context, meta = await asyncio.wait_for(
            deps["VoiceContextResolver"].resolve_context(ctx, participant),
            timeout=10.0
        )
        if not workspace_id:
            logger.warning(f"Closing avatar entrypoint - Context could not be resolved.")
            await ctx.room.local_participant.set_attributes({"lk.agent.state": "failed_resolution"})
            return

        settings = meta
        original_agent_id = agent_id

        db = deps["SessionLocal"]()
        try:
            if agent_id:
                agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].id == agent_id).first()
            else:
                agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].workspace_id == workspace_id).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                final_settings = {}
                if agent_rec.settings: final_settings.update(agent_rec.settings)
                final_settings.update(meta)
                settings = final_settings
                agent_id = original_agent_id or agent_id
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types or []
            
            skills = deps["SkillService"]().get_skills_for_agent(db, agent_id)
        finally: db.close()
        
        # Tracking & Logging
        log_id = deps["start_communication_log"](workspace_id, agent_id, settings, participant.identity)
        transcript = []

        # 4. Filtered Tools & Pipeline Setup
        voice_id = settings.get("voice_id", "Puck")
        from backend.tools.worker_tools import WorkerTools
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = deps["AgentTools"](workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        all_tools = deps["llm"].find_function_tools(agent_tools)

        # Inject MCP Tools
        enabled_slugs = [s.slug for s in skills] + (settings.get("allowed_worker_types") or [])
        if "skills" in settings and isinstance(settings["skills"], list):
            enabled_slugs = list(set(enabled_slugs + settings["skills"]))
            
        mcp_tools, mcp_instances, _ = await deps["MCPLoaderService"].load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools: all_tools.extend(mcp_tools)
        
        # Prompt build
        full_prompt = deps["get_avatar_prompt"](settings)

        # Inject cross-channel context memory
        try:
            from backend.services.agent_context_service import AgentContextService
            caller_id = participant.identity or settings.get("user_identifier")
            if caller_id:
                context_prompt = AgentContextService.build_context_prompt(
                    workspace_id=workspace_id, identifier=caller_id, channel="avatar", limit=10, hours=72, agent_id=agent_id
                )
                if context_prompt: full_prompt += f"\n\n{context_prompt}"
        except Exception as e:
            logger.warning(f"Context injection failed: {e}")

        # 5. Initialize Agent via Unified Multimodal Bridge
        logger.info("Initializing Avatar Agent via Multimodal Bridge...")
        agent = deps["VoicePipelineService"].get_multimodal_agent(
            workspace_id=workspace_id,
            voice_id=voice_id,
            prompt=full_prompt,
            vad=ctx.proc.userdata["vad"],
            fnc_ctx=agent_tools,
            chat_ctx=None
        )
        
        if not agent:
            raise RuntimeError("Failed to initialize MultimodalAgent")

        agent_tools.session = agent.session
        deps["VoiceHandlers"].register_session_events(agent, ctx)
        
        # Start the agent first to establish the AgentSession
        await agent.start(ctx.room)
        await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})
        
        # --- CRITICAL: Initialize Avatar (Replica Join) AFTER start (depends on session setup) ---
        resolved_provider = settings.get("avatar_provider", "anam")
        logger.info(f"Triggering Avatar Replica Join (Provider: {resolved_provider})")
        avatar_obj = await deps["initialize_avatar"](resolved_provider, settings, agent.session, ctx.room, ctx)
        
        logger.info("✅ Avatar agent active and listening.")
        
        # Trigger greeting (Wait for track publication to avoid initial silence)
        logger.info("Waiting for audio/video tracks to stabilize...")
        await asyncio.sleep(2.0)
        
        welcome_msg = settings.get("welcome_message", "Hello!")
        agent.say(welcome_msg)

        # 7. Wait & Cleanup
        shutdown_event = asyncio.Event()
        @ctx.room.on("disconnected")
        def on_disconnected(_):
            shutdown_event.set()
            
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN AVATAR AGENT ENTRYPOINT: {e}", exc_info=True)
        raise
    finally:
        if agent:
            logger.info("Entrypoint finally: Stopping agent...")
            await agent.stop()
        
        # Ensure deps is available for cleanup
        try:
            deps = get_avatar_deps()
            await deps["MCPLoaderService"].cleanup_mcp_servers(mcp_instances)
            await deps["finalize_communication_log"](log_id, transcript, avatar_obj if 'avatar_obj' in locals() else None)
        except Exception as cleanup_err:
            logger.debug(f"Cleanup error (expected if aborted early): {cleanup_err}")

if __name__ == "__main__":
    initialize_agent_env()
    from livekit.agents import cli, WorkerOptions
    from backend.utils.process_manager import ProcessManager
    
    pm = ProcessManager(name="avatar-agent", pid_file=os.path.join(_project_root, "avatar_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint, 
                prewarm_fnc=prewarm, 
                agent_name="avatar-agent",
                multiprocessing_context="forkserver",
                port=8082
            )
        )
    finally:
        pm.cleanup()
