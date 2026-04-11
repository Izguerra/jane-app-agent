import sys
import os
import logging
import asyncio
import json
import pytz
from datetime import datetime
from dotenv import load_dotenv
from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.plugins import deepgram

# Explicit .env path for LiveKit subprocess safety (multiprocessing.spawn on macOS)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"))

# DNS bypass removed for stability - relying on system DNS.

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.avatar.config import resolve_settings, get_llm, get_tts
from backend.avatar.providers import initialize_avatar
from backend.avatar.tracking import start_communication_log, finalize_communication_log
from backend.services.voice_handlers import VoiceHandlers
from backend.database import SessionLocal
from backend.agent_tools import AgentTools
from backend.services.mcp_loader_service import MCPLoaderService
from backend.services.skill_service import SkillService
from backend.models_db import Agent as AgentModel, Workspace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-agent")

def prewarm(proc: JobProcess):
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    try:
        logger.info(f"Avatar Agent Entrypoint: Room {ctx.room.name}")
        
        if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        
        await ctx.room.local_participant.set_attributes({"lk.agent.state": "initializing"})
        participant = await ctx.wait_for_participant()
        logger.info(f"Connecting avatar to human participant: {participant.identity}")
        
        # Resolve Settings & Agent Identity
        room_meta = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
        part_meta = json.loads(participant.metadata) if participant.metadata else {}
        settings = resolve_settings(room_meta, part_meta)
        workspace_id = settings.get("workspace_id")
        agent_id = settings.get("agent_id")

        # PRIMARY FIX: Extract agent_id from deterministic room name (same fix as voice_agent.py)
        # Room name format: "agent-session-{agent_id}-{mode}" (set by voice.py _generate_token)
        if not agent_id and ctx.room.name.startswith("agent-session-"):
            room_suffix = ctx.room.name[len("agent-session-"):]
            last_dash = room_suffix.rfind("-")
            if last_dash > 0:
                agent_id = room_suffix[:last_dash]
                logger.info(f"Extracted agent_id from room name: {agent_id}")

        if not agent_id and room_meta.get("agent_id"):
            agent_id = room_meta.get("agent_id")
            logger.info(f"Extracted agent_id from room metadata: {agent_id}")

        logger.info(f"Avatar resolved context: workspace_id={workspace_id}, agent_id={agent_id}")

        db = SessionLocal()
        try:
            # Use the correctly resolved agent_id
            if agent_id:
                agent_rec = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.workspace_id == workspace_id).first()
                if agent_rec:
                    logger.info(f"Loaded CORRECT agent record: {agent_rec.name} ({agent_rec.id})")
                else:
                    logger.warning(f"Agent {agent_id} not found in workspace {workspace_id}, falling back")
                    agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
            else:
                agent_rec = db.query(AgentModel).filter(AgentModel.workspace_id == workspace_id).first()
                if agent_rec:
                    logger.warning(f"No agent_id resolved, falling back to: {agent_rec.name} ({agent_rec.id})")
            
            if agent_rec:
                agent_id = agent_rec.id
                if agent_rec.settings: 
                    # Merge agent settings into current settings
                    settings.update(agent_rec.settings)
                # Inject top-level columns directly into settings
                settings["name"] = agent_rec.name
                settings["prompt_template"] = agent_rec.prompt_template
                settings["welcome_message"] = agent_rec.welcome_message
                settings["voice_id"] = agent_rec.voice_id
                settings["language"] = agent_rec.language
                settings["soul"] = agent_rec.soul
                settings["allowed_worker_types"] = agent_rec.allowed_worker_types
                logger.info(f"Avatar agent '{agent_rec.name}' has {len(agent_rec.allowed_worker_types or [])} worker types")
        finally:
            db.close()
        
        # Tracking
        log_id = start_communication_log(workspace_id, agent_id, settings, participant.identity)
        transcript = []

        # Pipeline Components — centralized via VoicePipelineService for key resolution consistency
        from backend.services.voice_pipeline_service import VoicePipelineService
        
        stt = VoicePipelineService.get_stt(workspace_id)
        llm_instance = VoicePipelineService.get_llm(workspace_id, settings)
        
        # Determine voice_id priority: avatar_voice_id -> avatarVoiceId (camelCase) -> voice_id -> default
        active_voice_id = settings.get("avatar_voice_id") or settings.get("avatarVoiceId") or settings.get("voice_id") or "Josh"
        tts_instance = VoicePipelineService.get_tts(workspace_id, active_voice_id, settings)
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
        raw_tools = llm.find_function_tools(agent_tools)
        
        # Inject MCP Tools (Granular Permission Check)
        mcp_tools, mcp_instances = await MCPLoaderService.load_mcp_servers(workspace_id, enabled_slugs)
        if mcp_tools:
            raw_tools.extend(mcp_tools)
            
        from backend.services.brain_service import BrainService
        allowed_tool_names = BrainService.get_allowed_tool_names(skills)
        
        all_tools = []
        for tool in raw_tools:
            tool_name = getattr(tool.info, "name", None) if hasattr(tool, "info") else getattr(tool, "name", None)
            if tool_name and tool_name in allowed_tool_names:
                all_tools.append(tool)
            elif tool_name is None:
                # Keep tools we can't inspect just in case (like edge MCP tools without generic info struct)
                all_tools.append(tool)
        
        logger.info(f"Loaded {len(all_tools)} tools for avatar agent (Filtered by skills)")
        
        # 3. Build Prompt with Local Workspace Reference Time
        ref_tz_name = settings.get("client_timezone", "America/Toronto")
        ref_tz = pytz.timezone(ref_tz_name)
        ref_time_str = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        
        db = SessionLocal()
        from backend.services.personality_service import PersonalityService
        from backend.services.brain_service import BrainService
        
        skills = SkillService().get_skills_for_agent(db, agent_id)
        personality = PersonalityService().get_personality(db, agent_id)
        personality_prompt = PersonalityService().generate_personality_prompt(personality)
        db.close()
        
        # Extract agent type and telephony context for persona switching (matches voice_agent.py)
        agent_type = settings.get("agent_type", "business")
        meta = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
        call_context = meta.get("call_context")
        
        logger.info(f"Building avatar prompt for Agent Type: {agent_type}, Ref Time ({ref_tz_name}): {ref_time_str}")

        full_prompt = BrainService.build_prompt(
            settings, personality_prompt, skills, 
            {"name": settings.get("name"), "phone": settings.get("phone"), "services": settings.get("services"), "role": settings.get("role")}, 
            ref_time_str,
            settings.get("client_location"),
            agent_type=agent_type,
            call_context=call_context
        )
        
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
        session = AgentSession(
            vad=vad, stt=stt, llm=llm_instance, tts=tts_instance, 
            tools=all_tools
        )
        # Inject session back into agent_tools for filler logic
        agent_tools.session = session

        agent_logic = livekit_Agent(instructions=full_prompt)
        
        # Register voice event handlers (matches voice_agent.py for consistent state tracking)
        VoiceHandlers.register_session_events(session, ctx)
        
        # === CRITICAL: Per LiveKit docs, avatar.start() MUST be called BEFORE session.start() ===
        # https://docs.livekit.io/agents/models/avatar/
        # Step 3: Start the avatar session, passing in the AgentSession instance
        # Step 4: Start the AgentSession
        
        # 3. Initialize Avatar FIRST (before session.start per LiveKit docs)
        resolved_provider = settings.get("avatar_provider") or ("anam" if settings.get("anam_persona_id") or settings.get("anamPersonaId") else "tavus")
        logger.info(f"Avatar provider resolved: '{resolved_provider}', anam_persona_id={settings.get('anam_persona_id')}, tavus_replica_id={settings.get('tavus_replica_id')}")
        avatar = await initialize_avatar(resolved_provider, settings, session, ctx.room, ctx)
        
        # 4. Start AgentSession AFTER avatar is initialized
        logger.info("Starting Avatar AgentSession pipeline...")
        await session.start(agent_logic, room=ctx.room)
        
        # 5. Brief delay for audio pipeline stabilization then greet
        await asyncio.sleep(0.8)
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
        # Prioritize LIVEKIT_AGENT_NAME then AGENT_NAME, default to the production-ready name
        agent_name = os.getenv("LIVEKIT_AGENT_NAME", os.getenv("AGENT_NAME", "supaagent-avatar-agent-v2"))
        
        cli.run_app(WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name=agent_name
        ))
    finally:
        pm.cleanup()
