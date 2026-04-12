import os
import json
import logging
from livekit.plugins import tavus, anam

logger = logging.getLogger("avatar-agent")

async def initialize_avatar(avatar_provider: str, settings: dict, session, room, ctx):
    from backend.services.integration_service import IntegrationService
    
    workspace_id = settings.get("workspace_id")
    tavus_replica_id = settings.get("tavus_replica_id") or settings.get("tavusReplicaId")
    tavus_persona_id = settings.get("tavus_persona_id") or settings.get("tavusPersonaId")
    anam_persona_id = settings.get("anam_persona_id") or settings.get("anamPersonaId")
    
    # GLOBAL PROTOCOL FIX: Ensure LiveKit URL uses WSS for all avatar providers
    url = os.environ.get("LIVEKIT_URL", "")
    if url.startswith("https://"):
        logger.info(f"Applying LiveKit WSS protocol fix: {url} -> wss://...")
        os.environ["LIVEKIT_URL"] = url.replace("https://", "wss://")

    avatar = None
    logger.info(f"DEBUG PROVIDER: provider='{avatar_provider}', workspace='{workspace_id}', anam_id='{anam_persona_id}', tavus_id='{tavus_replica_id}'")

    # Priority 1: Anam.ai
    if (avatar_provider == "anam" or not avatar_provider) and anam_persona_id:
        try:
            # Sourcing API Key from DB (with environment fallback)
            anam_key = IntegrationService.get_provider_key(workspace_id, "anam", "ANAM_API_KEY")
            if anam_key:
                os.environ["ANAM_API_KEY"] = anam_key
            
            name = settings.get("name", "JaneApp Agent")
            logger.info(f"Initializing Anam.ai avatar: persona={anam_persona_id}, name={name}")
            
            persona_cfg = anam.PersonaConfig(name=name, avatarId=anam_persona_id)
            avatar = anam.AvatarSession(persona_config=persona_cfg)
            
            logger.info(f"Starting Anam AvatarSession on room {room.name}...")
            await avatar.start(session, room=room)
            logger.info("Anam.ai Avatar session.start() completed successfully!")
            
        except Exception as e:
            import traceback
            logger.error(f"ANAM CRITICAL INITIALIZATION ERROR: {type(e).__name__}: {e}")
            logger.error(f"ANAM TRACEBACK:\n{traceback.format_exc()}")
            raise
            
    # Priority 2: Tavus
    elif tavus_replica_id:
        try:
            # Sourcing API Key from DB (with environment fallback)
            tavus_key = IntegrationService.get_provider_key(workspace_id, "tavus", "TAVUS_API_KEY")
            if tavus_key:
                os.environ["TAVUS_API_KEY"] = tavus_key
                
            logger.info(f"Initializing Tavus session with replica={tavus_replica_id}")
            avatar = tavus.AvatarSession(replica_id=tavus_replica_id, persona_id=tavus_persona_id)
            await avatar.start(session, room=room)
            logger.info("Tavus Avatar Started successfully!")
            
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
            raise
            
    return avatar
