import sys
import os
import logging
import asyncio
import json
from dotenv import load_dotenv
from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit import rtc
from livekit.plugins import deepgram

# Explicit .env path for LiveKit subprocess safety (multiprocessing.spawn on macOS)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

# --- DNS BYPASS FIX ---
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

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.avatar.config import resolve_settings, get_llm, get_tts
from backend.avatar.prompts import get_avatar_prompt
from backend.avatar.providers import initialize_avatar
from backend.avatar.tracking import start_communication_log, finalize_communication_log
from backend.services.voice_handlers import VoiceHandlers
from backend.database import SessionLocal
from backend.agent_tools import AgentTools
from backend.services.mcp_loader_service import MCPLoaderService
from backend.services.skill_service import SkillService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-agent")

def prewarm(proc: JobProcess):
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Setup process manager signals if it exists in global scope
    if 'pm' in globals():
        globals()['pm'].setup_signals(asyncio.get_event_loop())

    try:
        logger.info(f"Avatar Agent Entrypoint: Room {ctx.room.name}")
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        
        await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})
        participant = await ctx.wait_for_participant()
        
        # Resolve Settings & Agent Identity
        room_meta = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
        part_meta = json.loads(participant.metadata) if participant.metadata else {}
        settings = resolve_settings(room_meta, part_meta)
        workspace_id = settings.get("workspace_id")
        agent_id = settings.get("agent_id")

        db = SessionLocal()
        try:
            # Robust agent resolution: respect passed agent_id, or fallback to first in workspace
            if agent_id:
                agent_rec = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id).first()
            else:
                agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: 
                    # Merge agent settings into current settings
                    settings.update(agent_rec.settings)
                # Inject allowed_worker_types directly from the model into settings
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types
        finally:
            db.close()
        
        # Tracking
        log_id = start_communication_log(workspace_id, agent_id, settings, participant.identity)
        transcript = []

        # Pipeline Components — pass workspace_id for DB key retrieval
        stt = deepgram.STT(model="nova-2")
        llm_instance = get_llm(workspace_id=workspace_id)
        tts_instance = get_tts(settings.get("voice_id", "Josh"), workspace_id=workspace_id)
        vad = ctx.proc.userdata["vad"]
        
        logger.info(f"Avatar pipeline: LLM={type(llm_instance).__name__}, TTS={type(tts_instance).__name__}")
        
        # Tools & Skills
        from backend.tools.worker_tools import WorkerTools
        
        db = SessionLocal()
        skills = SkillService().get_skills_for_agent(db, agent_id)
        db.close()
        enabled_slugs = [s.slug for s in skills]
        
        worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
        agent_tools = AgentTools(workspace_id=workspace_id, communication_id=log_id, agent_id=agent_id, worker_tools=worker_tools)
        all_tools = llm.find_function_tools(agent_tools)
        
        # Inject MCP Tools (Granular Permission Check)
        mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools:
            all_tools.extend(mcp_tools)
        
        logger.info(f"Loaded {len(all_tools)} tools for avatar agent (Filtered by skills)")
        
        # Prompt
        full_prompt = get_avatar_prompt(settings)
        
        # Inject cross-channel context memory (Layer 2)
        try:
            from backend.services.agent_context_service import AgentContextService
            caller_id = participant.identity or settings.get("user_identifier")
            if caller_id:
                context_prompt = AgentContextService.build_context_prompt(
                    workspace_id=workspace_id, identifier=caller_id, channel="avatar", limit=10, hours=72
                )
                if context_prompt:
                    full_prompt += f"\n\n{context_prompt}"
                    logger.info(f"Injected cross-channel context for avatar caller: {caller_id}")
        except Exception as e:
            logger.warning(f"Context injection failed (non-fatal): {e}")
        
        from livekit.agents.voice import AgentSession, Agent as livekit_Agent
        session = AgentSession(vad=vad, stt=stt, llm=llm_instance, tts=tts_instance, tools=all_tools)
        # Inject session back into agent_tools for filler logic
        agent_tools.session = session

        agent_logic = livekit_Agent(instructions=full_prompt)
        
        # Register voice event handlers (matches voice_agent.py for consistent state tracking)
        VoiceHandlers.register_session_events(session, ctx)
        
        # 3. Start Agent Session first so tracks are published
        logger.info("Starting AgentSession pipeline...")
        await session.start(agent_logic, room=ctx.room)
        
        # Verify tracks for diagnostic purposes
        for lp in ctx.room.local_participant.track_publications.values():
            logger.info(f"Local track published: {lp.track.kind if lp.track else 'unknown'} (sid={lp.sid})")

        # 4. Initialize Avatar (hooks into existing published tracks)
        resolved_provider = settings.get("avatar_provider", "tavus")
        logger.info(f"Avatar provider resolved: '{resolved_provider}', anam_persona_id={settings.get('anam_persona_id')}, tavus_replica_id={settings.get('tavus_replica_id')}")
        avatar = await initialize_avatar(resolved_provider, settings, session, ctx.room, ctx)
        
        # 5. Brief delay for audio pipeline stabilization and Anam sync
        await asyncio.sleep(1.2)
        session.say(settings.get("welcome_message", "Hello!"), allow_interruptions=False)
        logger.info("Avatar agent fully started and greeted")

        @session.on("user_speech_committed")
        def on_user_speech(msg: llm.ChatMessage):
            transcript.append(f"USER: {msg.content}")

        @session.on("agent_speech_committed")
        def on_agent_speech(msg: llm.ChatMessage):
            transcript.append(f"AGENT: {msg.content}")

        shutdown_event = asyncio.Event()
        @ctx.room.on("disconnected")
        def on_room_disconnect(reason=None):
            shutdown_event.set()

        await shutdown_event.wait()
        
        from backend.services.mcp_loader_service import MCPLoaderService
        await MCPLoaderService.cleanup_mcp_servers(mcp_instances)
        await finalize_communication_log(log_id, transcript, avatar)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR IN AVATAR AGENT ENTRYPOINT: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise

from backend.utils.process_manager import ProcessManager

if __name__ == "__main__":
    pm = ProcessManager(name="avatar-agent", pid_file=os.path.join(_project_root, "avatar_agent.pid"))
    pm.check_lock()
    pm.write_lock()
    
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=os.getenv("AGENT_NAME", "supaagent-avatar-v2.1")))
    finally:
        pm.cleanup()

