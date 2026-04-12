import json
import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Path Setup
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe, JobContext, JobProcess, cli, WorkerOptions, llm
from backend.utils.process_manager import ProcessManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

_vad_model = None
def get_vad_model():
    global _vad_model
    if _vad_model is None:
        from livekit.plugins import silero
        _vad_model = silero.VAD.load(min_speech_duration=0.15, min_silence_duration=0.6 )
    return _vad_model

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = get_vad_model()

async def entrypoint(ctx: JobContext):
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
        
        # 1. Resolve Context
        workspace_id, agent_id, call_context, meta = await VoiceContextResolver.resolve_context(ctx, participant)

        # Safety Check: Use participant identity if agent_id still missing (some SIP trunks)
        if not agent_id and participant.identity.startswith("agnt_"):
            agent_id = participant.identity
            logger.info(f"Resolved agent_id={agent_id} from participant identity")

        logger.info(f"Resolved context: Workspace={workspace_id}, Agent={agent_id}")

        settings = get_settings(workspace_id, agent_id=agent_id)
        settings.update(meta)

        db = SessionLocal()
        log_id = settings.get("log_id")
        workspace_info = {"name": "Assistant", "phone": "N/A", "services": "General", "role": "AI Assistant"}

        try:
            agent_rec = None
            if agent_id:
                agent_rec = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id).first()
            
            # NO GREEDY FALLBACK. If no agent_id, we remain in a 'generic assistant' state.
            if agent_rec:
                if agent_rec.settings: settings.update(agent_rec.settings)
                for col in ["name", "prompt_template", "welcome_message", "voice_id", "language", "soul", "allowed_worker_types"]:
                    settings[col] = getattr(agent_rec, col, settings.get(col))
                
                ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                if ws:
                    workspace_info = {"name": ws.name, "phone": ws.phone, "services": settings.get("services"), "role": settings.get("role")}
            else:
                logger.warning(f"No specific agent record found for ID '{agent_id}'. Using generic persona.")

            if not log_id:
                log_entry = Communication(
                    id=generate_comm_id(), type="call", direction="outbound" if call_context else "inbound",
                    status="ongoing", started_at=start_time, workspace_id=workspace_id, agent_id=agent_id
                )
                db.add(log_entry)
                db.commit()
                log_id = log_entry.id
        finally: db.close()

        ref_tz = pytz.timezone(settings.get("client_timezone", "America/Toronto"))
        ref_time_str = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        
        db = SessionLocal()
        skills = SkillService().get_skills_for_agent(db, agent_id) if agent_id else []
        personality = PersonalityService().get_personality(db, agent_id) if agent_id else None
        personality_prompt = PersonalityService().generate_personality_prompt(personality) if personality else ""
        db.close()

        prompt = BrainService.build_prompt(
            settings, personality_prompt, skills, workspace_info, 
            ref_time_str, settings.get("client_location"),
            agent_type=settings.get("agent_type", "business"),
            call_context=meta.get("call_context")
        )

        from backend.tools.worker_tools import WorkerTools
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        raw_tools = llm.find_function_tools(agent_tools)

        enabled_slugs = [s.slug for s in skills]
        mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools: raw_tools.extend(mcp_tools)
            
        allowed_tool_names = BrainService.get_allowed_tool_names(skills)
        all_tools = [t for t in raw_tools if (getattr(t.info if hasattr(t, "info") else t, "name", None) in allowed_tool_names) or not getattr(t.info if hasattr(t, "info") else t, "name", None)]
        
        from livekit.agents.voice import AgentSession, Agent as VoiceAgent
        session = AgentSession(
            vad=get_vad_model(),
            stt=VoicePipelineService.get_stt(workspace_id),
            llm=VoicePipelineService.get_llm(workspace_id, settings),
            tts=VoicePipelineService.get_tts(workspace_id, settings.get("voice_id", "alloy"), settings),
            tools=all_tools
        )
        agent_tools.session = session
        VoiceHandlers.register_session_events(session, ctx)
        
        await session.start(VoiceAgent(instructions=prompt), room=ctx.room)
        await asyncio.sleep(0.5)
        session.say(settings.get("welcome_message", "Hello! How can I help you?"))

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
