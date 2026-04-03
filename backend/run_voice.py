import logging
import asyncio
import os
from voice_agent import entrypoint, prewarm
from livekit.agents import WorkerOptions, cli

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manual_voice_worker")

def run_worker():
    # Set the name explicitly so the dispatcher can find it
    os.environ["LIVEKIT_AGENT_NAME"] = "voice-agent"
    
    # Run using the same entrypoint logic
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        agent_name="voice-agent"
    ))

if __name__ == "__main__":
    run_worker()
