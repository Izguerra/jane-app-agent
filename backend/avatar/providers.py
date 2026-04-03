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
    
    # Provider-Strict Logic: Respect the explicitly selected provider
    if avatar_provider == "anam":
        final_anam_id = anam_persona_id or settings.get("anam_persona_id") or settings.get("anamPersonaId")
        if final_anam_id:
            try:
                logger.info(f"Initializing Anam.ai avatar with persona ID: {final_anam_id}")
                persona_cfg = anam.PersonaConfig(name=settings.get("name", "JaneApp Agent"), avatarId=final_anam_id)
                avatar = anam.AvatarSession(persona_config=persona_cfg)
                await avatar.start(session, room=room)
                logger.info(f"Anam.ai Avatar Started successfully!")
            except Exception as e:
                logger.error(f"ANAM ERROR: {e}")
        else:
            logger.warning("Anam provider selected but no persona ID found in settings.")
            
    elif avatar_provider == "tavus" or (not avatar_provider and tavus_replica_id):
        if tavus_replica_id:
            try:
                # WSS FIX
                url = os.environ.get("LIVEKIT_URL", "")
                if url.startswith("https://"):
                    os.environ["LIVEKIT_URL"] = url.replace("https://", "wss://")
                
                logger.info(f"Initializing Tavus session with replica={tavus_replica_id}")
                avatar = tavus.AvatarSession(replica_id=tavus_replica_id, persona_id=tavus_persona_id)
                await avatar.start(session, room=room)
                logger.info("Tavus Avatar Started!")
                
                # Metadata update for Tavus conversation ID
                cid = getattr(avatar, 'conversation_id', 'Unknown')
                if cid and cid != 'Unknown':
                    current_meta = json.loads(room.metadata) if room.metadata else {}
                    current_meta["tavus_conversation_id"] = cid
                    await room.update_metadata(json.dumps(current_meta))
            except Exception as e:
                import traceback
                logger.error(f"TAVUS ERROR: {e}")
                logger.error(f"TAVUS TRACEBACK:\n{traceback.format_exc()}")
            
    return avatar
