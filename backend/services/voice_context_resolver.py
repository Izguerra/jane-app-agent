import logging
import json
import asyncio
import os
from livekit.rtc import ConnectionState
from livekit.agents import AutoSubscribe
from backend.database import SessionLocal
from backend.models_db import Communication, Workspace, Agent as AgentModel, PhoneNumber

logger = logging.getLogger("voice-context-resolver")

class VoiceContextResolver:
    @staticmethod
    async def resolve_context(ctx, participant):
        """
        Resolves workspace_id, agent_id, and call_context based on room and participant data.
        """
        workspace_id = None
        agent_id = None
        call_context = None
        settings = {}

        # 1. Try room metadata
        if ctx.room.metadata:
            try:
                room_settings = json.loads(ctx.room.metadata)
                workspace_id = room_settings.get("workspace_id")
                agent_id = room_settings.get("agent_id")
                if workspace_id:
                    logger.info(f"Resolved workspace_id={workspace_id} from ROOM metadata")
                    settings = room_settings
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse room metadata: {e}")

        # 2. Strategy 1: Room Name (Outbound / Inbound)
        if not workspace_id:
            workspace_id, agent_id, call_context = await VoiceContextResolver._resolve_from_room_name(ctx.room.name)

        # 3. Strategy 2: SIP Attributes (LiveKit Native SIP Trunk)
        if not workspace_id:
            sip_workspace_id, sip_agent_id = await VoiceContextResolver._resolve_from_sip(participant)
            if sip_workspace_id:
                workspace_id = sip_workspace_id
                if sip_agent_id and not agent_id:
                    agent_id = sip_agent_id
                    logger.info(f"Resolved agent_id={agent_id} from SIP lookup")

        # 4. Strategy 3: Participant Metadata
        if not workspace_id and participant.metadata:
            workspace_id, agent_id, call_context, settings = VoiceContextResolver._resolve_from_participant_metadata(participant)

        # 5. Fallback Default Workspace (but NOT greedy agent)
        if not workspace_id:
            logger.warning("FALLBACK: No workspace_id resolved. Using default.")
            workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"

        return workspace_id, agent_id, call_context, settings

    @staticmethod
    async def _resolve_from_room_name(room_name):
        workspace_id = None
        agent_id = None
        call_context = None

        db = SessionLocal()
        try:
            if room_name.startswith("outbound-"):
                raw_id = room_name.replace("outbound-", "").replace("comm-", "comm_")
                comm_record = db.query(Communication).filter(Communication.id == raw_id).first()
                if comm_record:
                    workspace_id = comm_record.workspace_id
                    agent_id = comm_record.agent_id
                    call_context = comm_record.call_context
            elif room_name.startswith("inbound-") or room_name.startswith("call-"):
                comm_id = room_name.replace("inbound-", "").replace("comm-", "comm_")
                comm_record = db.query(Communication).filter(Communication.id == comm_id).first()
                if comm_record:
                    workspace_id = comm_record.workspace_id
                    agent_id = comm_record.agent_id
        finally:
            db.close()
        return workspace_id, agent_id, call_context

    @staticmethod
    async def _resolve_from_sip(participant):
        """Expanded SIP resolution supporting multiple possible LiveKit metadata keys."""
        # Check multiple possible keys used by various LiveKit SIP versions
        candidates = [
            participant.attributes.get("sip.callTo"),
            participant.attributes.get("sip.to"),
            participant.attributes.get("to"),
            participant.attributes.get("sip.callFrom"),
            participant.attributes.get("sip.from"),
            participant.attributes.get("from")
        ]
        
        logger.info(f"SIP Context Discovery - Candidates: {candidates}")
        
        db = SessionLocal()
        try:
            for phone in candidates:
                if not phone: continue
                # Clean SIP URI parts
                clean_phone = phone.split("@")[0].replace("sip:", "").replace("+", "").strip()
                # Test both with and without + prefix
                search_variants = [f"+{clean_phone}", clean_phone]
                
                p_rec = db.query(PhoneNumber).filter(PhoneNumber.phone_number.in_(search_variants)).first()
                if p_rec:
                    logger.info(f"MATCH: Phone '{phone}' matched Agent={p_rec.agent_id}")
                    return p_rec.workspace_id, p_rec.agent_id
        finally:
            db.close()
        return None, None

    @staticmethod
    def _resolve_from_participant_metadata(participant):
        try:
            meta = json.loads(participant.metadata)
            return meta.get("workspace_id"), meta.get("agent_id"), meta.get("call_context"), meta
        except:
            return None, None, None, {}
