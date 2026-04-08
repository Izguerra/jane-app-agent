import os
import json
import logging
from livekit.plugins import tavus, anam

logger = logging.getLogger("avatar-agent")

async def initialize_avatar(avatar_provider: str, settings: dict, session, room, ctx):
    tavus_replica_id = settings.get("tavus_replica_id") or settings.get("tavusReplicaId")
    tavus_persona_id = settings.get("tavus_persona_id") or settings.get("tavusPersonaId")
    anam_persona_id = settings.get("anam_persona_id") or settings.get("anamPersonaId")
    
    avatar = None
    if avatar_provider == "anam" and anam_persona_id:
        try:
            logger.info(f"Initializing Anam.ai avatar with persona={anam_persona_id}. Subscription: Auto")
            persona_cfg = anam.PersonaConfig(name=settings.get("name", "JaneApp Agent"), avatarId=anam_persona_id)
            avatar = anam.AvatarSession(persona_config=persona_cfg)
            
            # Subscribing to tracks logic is internal to LiveKit-Anam plugin
            await avatar.start(session, room=room)
            logger.info("Anam.ai Avatar Session started successfully (Video/Audio tracks requested)")
        except Exception as e:
            import traceback
            logger.error(f"ANAM ERROR: {e}")
            logger.error(f"ANAM TRACEBACK:\n{traceback.format_exc()}")
            # Don't silently swallow — the session will still work as voice-only
            
    elif tavus_replica_id:
        try:
            # WSS FIX
            url = os.environ.get("LIVEKIT_URL", "")
            if url.startswith("https://"):
                os.environ["LIVEKIT_URL"] = url.replace("https://", "wss://")
            
            logger.info(f"Initializing Tavus session with replica={tavus_replica_id}")
            avatar = tavus.AvatarSession(replica_id=tavus_replica_id, persona_id=tavus_persona_id)
            await avatar.start(session, room=room)
            logger.info(f"Tavus Avatar Session started successfully. Replica: {tavus_replica_id}")
            
            # Metadata update for Tavus conversation ID
            cid = getattr(avatar, 'conversation_id', 'Unknown')
            if cid and cid != 'Unknown':
                logger.debug(f"Tavus Conversation ID: {cid}")
                current_meta = json.loads(room.metadata) if room.metadata else {}
                current_meta["tavus_conversation_id"] = cid
                await room.update_metadata(json.dumps(current_meta))
        except Exception as e:
            import traceback
            logger.error(f"TAVUS ERROR: {e}")
            logger.error(f"TAVUS TRACEBACK:\n{traceback.format_exc()}")
            
    return avatar
