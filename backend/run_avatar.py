import logging
import asyncio
import os
from avatar_agent import entrypoint, prewarm
from livekit.agents import WorkerOptions, cli

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manual_avatar_worker")

def run_worker():
    # Set the name explicitly
    os.environ["LIVEKIT_AGENT_NAME"] = "avatar-agent"
    
    # Run using the same entrypoint logic
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        agent_name="avatar-agent"
    ))

if __name__ == "__main__":
    run_worker()
