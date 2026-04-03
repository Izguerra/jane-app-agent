import asyncio
import os
import subprocess
import logging
from fastapi import APIRouter, HTTPException
from livekit import api

router = APIRouter(prefix="/system", tags=["system"])
logger = logging.getLogger("system-router")

@router.post("/cleanup-zombies")
async def cleanup_zombies():
    """
    Kills any local zombie python agent processes and clears empty LiveKit rooms.
    """
    results = {
        "local_processes": "Skipped",
        "livekit_rooms": []
    }
    
    # 1. Use the Watchdog Agent's powerful cleanup logic
    try:
        from backend.workers.watchdog_worker import cleanup_orphaned_processes, cleanup_stale_livekit_rooms, sync_database_states
        
        # Run them all concurrently
        await asyncio.gather(
            cleanup_orphaned_processes(),
            cleanup_stale_livekit_rooms(),
            sync_database_states()
        )
        
        # Also do a hard kill for current session PID files as a safety fallback
        for pid_file in ["voice_agent.pid", "avatar_agent.pid"]:
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    os.kill(pid, 9) # Hard kill
                    os.remove(pid_file)
                except: pass

        results["local_processes"] = "Watchdog cleanup executed successfully"
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        results["local_processes"] = f"Error: {e}"
        
    return {"message": "Cleanup executed via Watchdog logic", "details": results}
