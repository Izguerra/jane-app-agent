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

def get_voice_deps():
    from livekit.rtc import ConnectionState
    from livekit.agents import AutoSubscribe, JobContext, JobProcess, cli, WorkerOptions, llm
    
    from backend.database import SessionLocal, generate_comm_id, DatabaseContext
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
        "DatabaseContext": DatabaseContext,
        "datetime": datetime,
        "timezone": timezone,
        "ConnectionState": ConnectionState,
        "AutoSubscribe": AutoSubscribe,
        "JobContext": JobContext,
        "llm": llm,
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
        import livekit.plugins.silero as silero
        _vad_model = silero.VAD.load()
    return _vad_model

def prewarm(proc):
    initialize_agent_env()
    proc.userdata["vad"] = get_vad_model()

async def entrypoint(ctx):
    # Ensure environment is initialized in the entrypoint process
    initialize_agent_env()
    
    # Setup process manager signals if it exists in the global scope
    if 'pm' in globals():
        globals()['pm'].setup_signals(asyncio.get_event_loop())
    
    agent = None
    mcp_instances = []
    log_id = None
    workspace_id = None
    start_time = datetime.now(timezone.utc)
        
    try:
        logger.info(f"🚀 [WORKER {os.getpid()}] Entrypoint started for room {ctx.room.name}")
        
        # 1. CONNECTION
        from livekit.agents import AutoSubscribe
        from livekit.rtc import ConnectionState
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
            logger.info("✅ Agent connected to room")

        # Explicitly log when participants join
        @ctx.room.on("participant_connected")
        def on_participant_connected(p):
            logger.info(f"👋 Participant connected: {p.identity}")

        # HANDSHAKE HARDENING: Wait for human participant
        participant = await ctx.wait_for_participant()
        logger.info(f"✅ Found participant: {participant.identity}")
        
        # Now we can safely set attributes on the local participant
        await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})

        # Lazy load dependencies within the spawned process
        deps = get_voice_deps()

        # 3. CONTEXT RESOLUTION (With Fallback)
        workspace_id = None
        agent_id = None
        call_context = None
        meta = {}
        
        for attempt in range(1, 4):
            try:
                # Use a hard timeout for context resolution to prevent logic hangs
                workspace_id, agent_id, call_context, meta = await asyncio.wait_for(
                    deps["VoiceContextResolver"].resolve_context(ctx, participant),
                    timeout=3.0
                )
                if workspace_id and workspace_id != "wrk_000V7dMzXJLzP5mYgdf7FzjA3J":
                    logger.info(f"✅ Context resolved on attempt {attempt}")
                    break
            except Exception as e:
                logger.warning(f"⚠️ Context resolution attempt {attempt} failed: {e}")
            
            if attempt < 3:
                await asyncio.sleep(1.0)

        if not workspace_id:
            workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"

        settings = deps["get_settings"](workspace_id)
        settings.update(meta)

        # 2. Database & Logging (run in thread to avoid blocking event loop)
        log_id = settings.get("log_id")
        workspace_info = {"name": "The Business", "phone": "N/A", "services": "General", "role": "Assistant"}
        skills = []
        personality_prompt = "\n## IDENTITY & PERSONALITY\nYou are a professional digital assistant."

        def _sync_db_init():
            nonlocal log_id, workspace_info, skills, personality_prompt, settings, agent_id
            db = deps["SessionLocal"]()
            try:
                if not agent_id:
                    agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].workspace_id == workspace_id).first()
                    if agent_rec:
                        agent_id = agent_rec.id
                else:
                    agent_rec = db.query(deps["AgentModel"]).filter(deps["AgentModel"].id == agent_id).first()
                
                if agent_rec:
                    if agent_rec.settings: 
                        settings.update(agent_rec.settings)
                    settings["allowed_worker_types"] = agent_rec.allowed_worker_types or []
                    
                    ws = db.query(deps["Workspace"]).filter(deps["Workspace"].id == workspace_id).first()
                    if ws: 
                        workspace_info = {
                            "name": ws.name, 
                            "phone": ws.phone or "N/A", 
                            "services": settings.get("services", "General"), 
                            "role": settings.get("role", "Assistant")
                        }
                
                if not log_id:
                    log_entry = deps["Communication"](
                        id=deps["generate_comm_id"](), 
                        type="call", 
                        direction="outbound" if call_context else "inbound",
                        status="ongoing", 
                        started_at=start_time, 
                        workspace_id=workspace_id, 
                        agent_id=agent_id
                    )
                    db.add(log_entry)
                    db.commit()
                    log_id = log_entry.id
                    
                skills = deps["SkillService"]().get_skills_for_agent(db, agent_id) if agent_id else []
                personality = deps["PersonalityService"]().get_personality(db, agent_id)
                personality_prompt = deps["PersonalityService"]().generate_personality_prompt(personality)
            except Exception as db_err:
                logger.error(f"Error during DB initialization: {db_err}")
            finally: 
                db.close()

        await asyncio.to_thread(_sync_db_init)

        prompt = deps["VoicePromptBuilder"].build_prompt(
            settings, personality_prompt, skills, workspace_info, 
            start_time.strftime("%A, %B %d, %Y at %I:%M %p"), settings.get("client_location")
        )

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

        # 4. Agent Initialization
        agent = deps["VoicePipelineService"].get_multimodal_agent(
            workspace_id=workspace_id,
            voice_id=voice_id,
            prompt=prompt, # Using the context-aware prompt built earlier
            vad=get_vad_model()
        )

        # Update participant identity/metadata for frontend tracking
        await ctx.room.local_participant.set_attributes({
            "lk.agent.state": "initializing",
            "agent": "true"
        })

        # PRECISE LIFECYCLE: Set initializing before start, listening after success
        logger.info("🚀 Starting AgentSession handshake...")
        await ctx.room.local_participant.set_attributes({"lk.agent.state": "initializing"})
        
        # START HANDSHAKE (Explicitly passing participant fixes the Cold Call hang)
        # Passing the correctly initialized agent and participant
        if not agent:
            raise RuntimeError("Failed to initialize MultimodalAgent")

        deps["VoiceHandlers"].register_session_events(agent, ctx)
        
        # --- START HANDSHAKE ---
        welcome_msg = settings.get("welcome_message", "Hello! How can I help you?")
        
        # ADD DELAY: Ensure the multimodal session is fully ready before the first greeting
        # This prevents the NoneType response_id error in livekit-agents 1.5.1
        await asyncio.sleep(1.0)
        
        logger.info("Voice say greeting triggered") # Signal for E2E tests
        agent.say(welcome_msg)
        await agent.start(ctx.room, participant)
        
        # LINK SESSION ONLY AFTER START
        agent_tools.session = agent.session
        
        await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})
        logger.info("✅ AgentSession handshake complete. State: Listening.")

        # 6. Wait & Cleanup
        shutdown_event = asyncio.Event()
        @ctx.room.on("disconnected")
        def on_disconnected(_):
            shutdown_event.set()
            
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN VOICE AGENT ENTRYPOINT: {e}", exc_info=True)
        raise
    finally:
        if agent:
            logger.info("Entrypoint finally: Stopping agent...")
            await agent.stop()
        
        # Ensure deps is available for cleanup
        try:
            deps = get_voice_deps()
            await deps["MCPLoaderService"].cleanup_mcp_servers(mcp_instances)
            # Attempt to save transcript if session data is available
            await deps["VoiceHandlers"].capture_and_save_transcript(agent.session if agent else None, log_id, workspace_id, start_time)
        except Exception as cleanup_err:
            logger.debug(f"Cleanup error (expected if aborted early): {cleanup_err}")

if __name__ == "__main__":
    initialize_agent_env()
    from livekit.agents import cli, WorkerOptions
    from backend.utils.process_manager import ProcessManager
    
    pm = ProcessManager(name="voice-agent", pid_file=os.path.join(_project_root, "voice_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint, 
                prewarm_fnc=prewarm, 
                agent_name="voice-agent",
                multiprocessing_context="forkserver",
                port=8081
            )
        )
    finally:
        pm.cleanup()
