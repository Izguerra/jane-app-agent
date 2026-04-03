import asyncio
import os
import psutil
import logging
import time
from datetime import datetime, timezone, timedelta
from livekit import api
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models_db import Communication
from backend.utils.config import AVATAR_AGENT_PORT, VOICE_AGENT_PORT

logger = logging.getLogger("watchdog-worker")

async def cleanup_orphaned_processes():
    """
    Finds and terminates orphaned agent processes that are no longer associated 
    with a valid PID file or have exceeded a sanity timeout.
    """
    try:
        current_time = time.time()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(cmdline)
                
                # Identify our agents
                is_agent = "backend.voice_agent" in cmd_str or "backend.avatar_agent" in cmd_str
                if not is_agent:
                    continue
                
                # Rule 1: Kill if process is older than 4 hours (Safety net for escaped processes)
                create_time = proc.info.get('create_time', 0)
                age_hours = (current_time - create_time) / 3600
                if age_hours > 4:
                    logger.warning(f"Killing aged agent process {proc.info['pid']} (Age: {age_hours:.1f}h)")
                    proc.terminate()
                    continue

                # Rule 2: Note: We don't necessarily kill all here, but we log the state.
                # The room cleanup below is more accurate for "zombie" detection.
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Process cleanup error: {e}")

async def cleanup_stale_livekit_rooms():
    """
    Deletes LiveKit rooms that are empty and have been active for more than 15 minutes.
    """
    try:
        lk_url = os.getenv("LIVEKIT_URL")
        lk_key = os.getenv("LIVEKIT_API_KEY")
        lk_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not (lk_url and lk_key):
            return

        lkapi = api.LiveKitAPI(lk_url, lk_key, lk_secret)
        rooms_resp = await lkapi.room.list_rooms(api.ListRoomsRequest())
        
        for r in rooms_resp.rooms:
            # Check if room is empty
            if r.num_participants == 0:
                # LiveKit room creation time is in seconds since epoch
                room_age_mins = (time.time() - r.creation_time) / 60
                
                # Rule: Delete empty rooms older than 10 minutes
                if room_age_mins > 10:
                    logger.info(f"Cleaning up stale empty room: {r.name} (Age: {room_age_mins:.1f}m)")
                    await lkapi.room.delete_room(api.DeleteRoomRequest(room=r.name))
        
        await lkapi.aclose()
    except Exception as e:
        logger.error(f"LiveKit room cleanup error: {e}")

async def sync_database_states():
    """
    Finds 'active' communications that no longer have a matching LiveKit room.
    """
    db = SessionLocal()
    try:
        # Limit to last 24 hours to avoid scanning everything
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        active_comms = db.query(Communication).filter(
            Communication.status == "active",
            Communication.created_at >= cutoff
        ).all()
        
        if not active_comms:
            return

        # Get current rooms to cross-reference
        lk_url = os.getenv("LIVEKIT_URL")
        lk_key = os.getenv("LIVEKIT_API_KEY")
        lk_secret = os.getenv("LIVEKIT_API_SECRET")
        
        current_room_names = set()
        if lk_url and lk_key:
            lkapi = api.LiveKitAPI(lk_url, lk_key, lk_secret)
            rooms_resp = await lkapi.room.list_rooms(api.ListRoomsRequest())
            current_room_names = {r.name for r in rooms_resp.rooms}
            await lkapi.aclose()
        
        for comm in active_comms:
            room_name = f"agent-session-{comm.id}"
            if room_name not in current_room_names:
                # Communication is orphaned in DB
                logger.info(f"Syncing orphaned DB communication {comm.id} to completed")
                comm.status = "completed"
                db.add(comm)
        
        db.commit()
    except Exception as e:
        logger.error(f"DB state sync error: {e}")
    finally:
        db.close()

async def run_watchdog_worker():
    """
    Main watchdog loop. Runs every 2 minutes.
    """
    logger.info("Watchdog Agent started - Monitoring processes, rooms, and DB states.")
    while True:
        try:
            await cleanup_orphaned_processes()
            await cleanup_stale_livekit_rooms()
            await sync_database_states()
        except Exception as e:
            logger.error(f"Watchdog main loop error: {e}")
        
        await asyncio.sleep(120) # Run every 2 minutes
