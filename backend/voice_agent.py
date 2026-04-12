import json
import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── Path & Env Setup ──
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe, JobContext, JobProcess, cli, WorkerOptions, llm
from backend.utils.process_manager import ProcessManager

# ── Import Optimization ──
# Service-specific heavy imports are moved into local scopes to speed up WorkerProcess spawning.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# ── VAD Setup ──
_vad_model = None
def get_vad_model():
    global _vad_model
    if _vad_model is None:
        from livekit.plugins import silero  # Lazy import — safe for macOS spawn
        # TUNE FOR SNAPPINESS
        _vad_model = silero.VAD.load(
            min_speech_duration=0.15,
            min_silence_duration=0.6,
            prefix_padding_ms=200,
            max_buffered_speech_pd=30
        )
    return _vad_model

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = get_vad_model()

async def entrypoint(ctx: JobContext):
    # Local imports for performance optimization
    import pytz
    from backend.database import SessionLocal, generate_comm_id
    from backend.models_db import Communication, Agent as AgentModel, Workspace
    from backend.settings_store import get_settings
    from backend.services.voice_context_resolver import VoiceContextResolver
    from backend.services.brain_service import BrainService
    from backend.services.voice_pipeline_service import VoicePipelineService
    from backend.services.voice_handlers import VoiceHandlers
    from backend.agent_tools import AgentTools
    from backend.services.skill_service import SkillService
    from backend.services.personality_service import PersonalityService
    from backend.services.mcp_loader_service import MCPLoaderService

    try:
        logger.info(f"Entrypoint started for room {ctx.room.name}")
        start_time = datetime.now(timezone.utc)
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        await ctx.room.local_participant.set_attributes({"lk.agent.state": "initializing"})
        participant = await ctx.wait_for_participant()
        logger.info(f"Connecting to human participant: {participant.identity}")

        # 1. Resolve Context
        workspace_id, agent_id, call_context, meta = await VoiceContextResolver.resolve_context(ctx, participant)

        # PRIMARY FIX: Extract agent_id from deterministic room name BEFORE get_settings()
        if not agent_id and ctx.room.name.startswith("agent-session-"):
            parts = ctx.room.name.split("-")
            room_suffix = ctx.room.name[len("agent-session-"):]
            last_dash = room_suffix.rfind("-")
            if last_dash > 0:
                agent_id = room_suffix[:last_dash]
                logger.info(f"Extracted agent_id from room name: {agent_id}")

        if not agent_id and meta.get("agent_id"):
            agent_id = meta.get("agent_id")
            logger.info(f"Extracted agent_id from room metadata: {agent_id}")

        logger.info(f"Resolved context: workspace_id={workspace_id}, agent_id={agent_id}")

        # Load workspace-level defaults
        settings = get_settings(workspace_id, agent_id=agent_id)
        settings.update(meta)

        # 2. Database & Logging
        db = SessionLocal()
        log_id = settings.get("log_id")
        workspace_info = {"name": "The Business", "phone": "N/A", "services": "General", "role": "Assistant"}

        try:
            if agent_id:
                agent_rec = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id).first()
            else:
                agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: settings.update(agent_rec.settings)
                settings["name"] = agent_rec.name
                settings["prompt_template"] = agent_rec.prompt_template
                settings["welcome_message"] = agent_rec.welcome_message
                settings["voice_id"] = agent_rec.voice_id
                settings["language"] = agent_rec.language
                settings["soul"] = agent_rec.soul
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types
                
                ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                if ws:
                    workspace_info = {"name": ws.name, "phone": ws.phone, "services": settings.get("services"), "role": settings.get("role")}
                
            if not log_id:
                log_entry = Communication(
                    id=generate_comm_id(), type="call", direction="outbound" if call_context else "inbound",
                    status="ongoing", started_at=start_time, workspace_id=workspace_id, agent_id=agent_id
                )
                db.add(log_entry)
                db.commit()
                log_id = log_entry.id
        finally: db.close()

        # 3. Build Prompt
        ref_tz_name = settings.get("client_timezone", "America/Toronto")
        ref_tz = pytz.timezone(ref_tz_name)
        ref_time_str = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        
        db = SessionLocal()
        skills = SkillService().get_skills_for_agent(db, agent_id)
        personality = PersonalityService().get_personality(db, agent_id)
        personality_prompt = PersonalityService().generate_personality_prompt(personality)
        db.close()

        agent_type = settings.get("agent_type", "business")
        call_context = meta.get("call_context")

        prompt = BrainService.build_prompt(
            settings, personality_prompt, skills, workspace_info, 
            ref_time_str, settings.get("client_location"),
            agent_type=agent_type,
            call_context=call_context
        )

        # 4. Filtered Tools & Pipeline Setup
        voice_id = settings.get("voice_id", "alloy")
        
        from backend.tools.worker_tools import WorkerTools
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        raw_tools = llm.find_function_tools(agent_tools)

        enabled_slugs = [s.slug for s in skills]
        mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools:
            raw_tools.extend(mcp_tools)
            
        allowed_tool_names = BrainService.get_allowed_tool_names(skills)
        
        all_tools = []
        for tool in raw_tools:
            tool_name = getattr(tool.info, "name", None) if hasattr(tool, "info") else getattr(tool, "name", None)
            if tool_name and tool_name in allowed_tool_names:
                all_tools.append(tool)
            elif tool_name is None:
                all_tools.append(tool)
        
        from livekit.agents.voice import AgentSession, Agent as VoiceAgent
        session = AgentSession(
            vad=get_vad_model(),
            stt=VoicePipelineService.get_stt(workspace_id),
            llm=VoicePipelineService.get_llm(workspace_id, settings),
            tts=VoicePipelineService.get_tts(workspace_id, voice_id, settings),
            tools=all_tools
        )
        agent_tools.session = session
        
        VoiceHandlers.register_session_events(session, ctx)
        await session.start(VoiceAgent(instructions=prompt), room=ctx.room)
        await asyncio.sleep(0.5)
        session.say(settings.get("welcome_message", "Hello! How can I help you?"))

        # 5. Wait & Cleanup
        shutdown_event = asyncio.Event()
        ctx.room.on("disconnected", lambda _: shutdown_event.set())
        await shutdown_event.wait()
        
        await MCPLoaderService.cleanup_mcp_servers(mcp_instances)
        await VoiceHandlers.capture_and_save_transcript(locals().get('session'), log_id, workspace_id, start_time)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN VOICE AGENT ENTRYPOINT: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    pm = ProcessManager(name="voice-agent", pid_file=os.path.join(_project_root, "voice_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        agent_name = os.getenv("LIVEKIT_AGENT_NAME", os.getenv("AGENT_NAME", "supaagent-voice-agent-v2"))
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=agent_name))
    finally:
        pm.cleanup()
