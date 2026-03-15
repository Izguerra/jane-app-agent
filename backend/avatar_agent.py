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

load_dotenv()

# --- DNS BYPASS FIX ---
import socket
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "jane-clinic-app-tupihomh.livekit.cloud":
        host = "161.115.178.157"
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar-agent")

def prewarm(proc: JobProcess):
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    logger.info(f"Avatar Agent Entrypoint: Room {ctx.room.name}")
    
    if ctx.room.connection_state != ConnectionState.CONN_CONNECTED:
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    
    await ctx.room.local_participant.set_attributes({"agent": "true", "lk.agent.state": "initializing"})
    participant = await ctx.wait_for_participant()
    
    # Resolve Settings
    room_meta = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
    part_meta = json.loads(participant.metadata) if participant.metadata else {}
    settings = resolve_settings(room_meta, part_meta)
    workspace_id = settings.get("workspace_id")
    agent_id = settings.get("agent_id")
    
    # Tracking
    log_id = start_communication_log(workspace_id, agent_id, settings, participant.identity)
    transcript = []

    # Pipeline Components
    stt = deepgram.STT(model="nova-2")
    llm_instance = get_llm()
    tts_instance = get_tts(settings.get("voice_id", "Josh"))
    vad = ctx.proc.userdata["vad"]
    
    # Tools
    from backend.agent_tools import AgentTools
    from backend.tools.worker_tools import WorkerTools
    worker_tools = WorkerTools(workspace_id=workspace_id, allowed_worker_types=settings.get("allowed_worker_types", []))
    agent_tools = AgentTools(workspace_id=workspace_id, agent_id=agent_id, worker_tools=worker_tools)
    all_tools = llm.find_function_tools(agent_tools)
    
    # Prompt
    full_prompt = get_avatar_prompt(settings)
    
    from livekit.agents.voice import AgentSession, Agent as livekit_Agent
    session = AgentSession(vad=vad, stt=stt, llm=llm_instance, tts=tts_instance, tools=all_tools)
    agent_logic = livekit_Agent(instructions=full_prompt)
    
    # Avatar initialization
    avatar = await initialize_avatar(settings.get("avatar_provider", "tavus"), settings, session, ctx.room, ctx)
    
    await session.start(agent_logic, room=ctx.room)
    await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})
    session.say(settings.get("welcome_message", "Hello!"), allow_interruptions=False)

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
    await finalize_communication_log(log_id, transcript, avatar)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=os.getenv("AGENT_NAME", "supaagent-avatar-agent-v2")))
