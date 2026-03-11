import logging
import json
import asyncio
import os
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
import backend.voice_agent as voice_agent_module
import backend.avatar_agent as avatar_agent_module

# Configure logging
logger = logging.getLogger("main-agent")
logger.setLevel(logging.INFO)

def prewarm(proc: JobProcess):
    """
    Prewarm shared resources (VAD).
    """
    logger.info("Main Agent Prewarm: Loading VAD...")
    try:
        # Use voice agent's logic to load VAD into proc.userdata
        voice_agent_module.prewarm(proc)
        logger.info("Main Agent Prewarm: VAD Loaded.")
    except Exception as e:
        logger.error(f"Main Agent Prewarm Failed: {e}")

async def entrypoint(ctx: JobContext):
    """
    Unified Entrypoint.
    Connects to the room, checks metadata, and dispatches to the correct agent logic.
    """
    logger.info(f"Main Agent Entrypoint: Room {ctx.room.name}, Job {ctx.job.id}")

    try:
        # 1. Connect to get metadata
        logger.info(f"Main Agent: Connecting to Room {ctx.room.name}...")
        print("DEBUG: Calling ctx.connect()...", flush=True)
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        print("DEBUG: ctx.connect() returned.", flush=True)
        logger.info("Main Agent Connected to Room.")
        
        # 2. Determine Mode
        mode = "voice" # Default
        print(f"DEBUG: Processing Metadata: {ctx.room.metadata}", flush=True)
        if ctx.room.metadata:
            try:
                meta = json.loads(ctx.room.metadata)
                mode = meta.get("mode", "voice")
            except Exception as e:
                logger.error(f"Failed to parse room metadata: {e}")
        
        logger.info(f"Detected Mode: {mode.upper()}")
        print(f"DEBUG: Mode is {mode}", flush=True)

        # 3. Dispatch
        if mode == "avatar":
            logger.info(">>> DISPATCHING TO AVATAR AGENT <<<")
            print("DEBUG: Calling avatar_agent.entrypoint...", flush=True)
            await avatar_agent_module.entrypoint(ctx)
        else:
            logger.info(">>> DISPATCHING TO VOICE AGENT <<<")
            print("DEBUG: Calling voice_agent.entrypoint...", flush=True)
            await voice_agent_module.entrypoint(ctx)

    except Exception as e:
        logger.error(f"Main Agent Critical Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Ensure we don't leave the room hanging if we crashed before dispatch
        # But if we dispatched, the sub-agent handles it.
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Run as "supaagent-voice-agent" because that's what LiveKit Cloud allows
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="supaagent-voice-agent"
        )
    )
