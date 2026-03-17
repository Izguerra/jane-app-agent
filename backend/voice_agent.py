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
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.178.157', port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.179.230', port))
        ]
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _patched_getaddrinfo

# Path Setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

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

        participant = await ctx.wait_for_participant()
        await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})

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
            agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: settings.update(agent_rec.settings)
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

        # 4. Pipeline Setup
        voice_id = settings.get("voice_id", "alloy")
        all_tools = llm.find_function_tools(AgentTools(workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id))
        
        logger.info("Initializing AgentSession pipeline")
        agent = await VoicePipelineService.get_multimodal_agent(workspace_id, voice_id, prompt, all_tools)
        if agent:
            logger.info("Starting Multimodal Agent")
            await agent.start(ctx.room, participant)
        else:
            logger.info("Starting Standard AgentSession")
            from livekit.agents.voice import AgentSession, Agent as VoiceAgent
            session = AgentSession(
                vad=get_vad_model(), stt=VoicePipelineService.get_stt(workspace_id),
                llm=VoicePipelineService.get_llm(workspace_id, settings),
                tts=VoicePipelineService.get_tts(workspace_id, voice_id, settings),
                tools=all_tools
            )
            VoiceHandlers.register_session_events(session, ctx)
            await session.start(VoiceAgent(instructions=prompt), room=ctx.room)
            await asyncio.sleep(0.8)
            session.say(settings.get("welcome_message", "Hello! How can I help you?"))

        # 5. Wait & Cleanup
        shutdown_event = asyncio.Event()
        ctx.room.on("disconnected", lambda _: shutdown_event.set())
        await shutdown_event.wait()
        await VoiceHandlers.capture_and_save_transcript(locals().get('session'), log_id, workspace_id, start_time)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN VOICE AGENT ENTRYPOINT: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=os.getenv("AGENT_NAME", "supaagent-voice-agent-v2")))
