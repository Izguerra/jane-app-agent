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

# DNS bypass removed for stability - relying on system DNS.

# Path Setup — explicit paths for LiveKit subprocess safety (multiprocessing.spawn)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

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
        settings = get_settings(workspace_id)
        settings.update(meta)

        # 2. Database & Logging
        db = SessionLocal()
        log_id = settings.get("log_id")
        customer_id = None
        workspace_info = {"name": "The Business", "phone": "N/A", "services": "General", "role": "Assistant"}

        try:
            # Correct logic: Use agent_id if provided by resolver, otherwise fallback to first in workspace
            if agent_id:
                agent_rec = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id).first()
            else:
                agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: settings.update(agent_rec.settings)
                # Inject top-level columns directly into settings for the pipeline
                settings["voice_id"] = agent_rec.voice_id
                settings["language"] = agent_rec.language
                settings["soul"] = agent_rec.soul
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types
                # Query Workspace directly — Agent model has no 'workspace' relationship
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
        db = SessionLocal()
        skills = SkillService().get_skills_for_agent(db, agent_id)
        personality = PersonalityService().get_personality(db, agent_id)
        personality_prompt = PersonalityService().generate_personality_prompt(personality)
        db.close()

        prompt = VoicePromptBuilder.build_prompt(
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
                    workspace_id=workspace_id, identifier=caller_id, channel="voice", limit=10, hours=72
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
        agent_tools = AgentTools(workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        all_tools = llm.find_function_tools(agent_tools)

        # Inject MCP Tools (Granular Permission Check)
        enabled_slugs = [s.slug for s in skills]
        mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools:
            all_tools.extend(mcp_tools)
        
        logger.info(f"Loading {len(all_tools)} tools for Voice Agent (Filtered by skills)")
        
        logger.info("Initializing Stable AgentSession")
        from livekit.agents.voice import AgentSession, Agent as VoiceAgent
        session = AgentSession(
            vad=get_vad_model(),
            stt=VoicePipelineService.get_stt(workspace_id),
            llm=VoicePipelineService.get_llm(workspace_id, settings),
            tts=VoicePipelineService.get_tts(workspace_id, voice_id, settings),
            tools=all_tools
        )
        # Inject session back into agent_tools for filler logic
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
        import traceback
        traceback.print_exc()
        raise

from backend.utils.process_manager import ProcessManager

if __name__ == "__main__":
    pm = ProcessManager(name="voice-agent", pid_file=os.path.join(_project_root, "voice_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        # Prioritize LIVEKIT_AGENT_NAME then AGENT_NAME, default to the production-ready name
        agent_name = os.getenv("LIVEKIT_AGENT_NAME", os.getenv("AGENT_NAME", "supaagent-voice-agent-v2"))
        
        cli.run_app(WorkerOptions(
            entrypoint_fnc=entrypoint, 
            prewarm_fnc=prewarm,
            agent_name=agent_name
        ))
    finally:
        pm.cleanup()
