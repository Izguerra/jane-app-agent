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

        # 2. Strategy 1 & 1b: Room Name (Outbound / Inbound)
        if not workspace_id:
            workspace_id, agent_id, call_context = await VoiceContextResolver._resolve_from_room_name(ctx.room.name)

        # 3. Strategy 2: SIP Attributes (LiveKit Native SIP Trunk)
        if not workspace_id:
            sip_workspace_id, sip_agent_id = await VoiceContextResolver._resolve_from_sip(participant)
            if sip_workspace_id:
                workspace_id = sip_workspace_id
                if sip_agent_id and not agent_id:
                    agent_id = sip_agent_id
                    logger.info(f"Resolved agent_id={agent_id} from SIP phone number lookup")

        # 4. Strategy 3: Participant Metadata
        if not workspace_id and participant.metadata:
            workspace_id, agent_id, call_context, settings = VoiceContextResolver._resolve_from_participant_metadata(participant)

        # 5. Fallback
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
            # Outbound
            if room_name.startswith("outbound-"):
                raw_id = room_name.replace("outbound-", "").replace("outbound--", "")
                comm_id = raw_id.replace("comm-", "comm_") if raw_id.startswith("comm-") else raw_id
                
                # Check for phone number style room name
                if "+" in raw_id:
                    parts = room_name.split('_')
                    phone_match = next((p for p in parts if p.startswith('+')), None)
                    if phone_match:
                        comm_record = db.query(Communication).filter(
                            Communication.user_identifier.like(f"{phone_match}%"),
                            Communication.direction == "outbound"
                        ).order_by(Communication.started_at.desc()).first()
                        if comm_record:
                            return comm_record.workspace_id, comm_record.agent_id, comm_record.call_context

                comm_record = db.query(Communication).filter(Communication.id == comm_id).first()
                if comm_record:
                    workspace_id = comm_record.workspace_id
                    agent_id = comm_record.agent_id
                    call_context = comm_record.call_context or (
                        {"intent": comm_record.call_intent, "customer_id": comm_record.customer_id}
                        if comm_record.call_intent else None
                    )
            
            # Inbound (Telnyx/Generic)
            elif room_name.startswith("call-") or room_name.startswith("inbound-"):
                reconstructed_call_id = None
                if room_name.startswith("call-"):
                    raw_id = room_name[5:]
                    reconstructed_call_id = "v3:" + raw_id[3:] if raw_id.startswith("v3-") else raw_id
                
                comm_id = room_name.replace("inbound-", "").replace("comm-", "comm_")
                comm_record = db.query(Communication).filter(
                    (Communication.id == comm_id) | 
                    (Communication.telnyx_call_id == reconstructed_call_id)
                ).first()
                
                if comm_record:
                    workspace_id = comm_record.workspace_id
                    agent_id = comm_record.agent_id
        except Exception as e:
            logger.error(f"Room name resolution error: {e}")
        finally:
            db.close()
        
        return workspace_id, agent_id, call_context

    @staticmethod
    async def _resolve_from_sip(participant):
        """Resolve workspace and agent from SIP participant attributes.
        
        When calls arrive via LiveKit's native SIP trunk, the participant
        has sip.callTo (dialed number) and sip.callFrom (caller number).
        We look up the PhoneNumber table to find the workspace and agent.
        """
        sip_to = participant.attributes.get("sip.callTo") or participant.attributes.get("to")
        sip_from = participant.attributes.get("sip.callFrom") or participant.attributes.get("from")
        
        logger.info(f"SIP resolution: callTo={sip_to}, callFrom={sip_from}")
        
        db = SessionLocal()
        try:
            # First check the dialed number (sip_to) — this maps to our registered phone number
            for phone_candidate in [sip_to, sip_from]:
                if not phone_candidate: continue
                clean_phone = phone_candidate.split("@")[0].replace("sip:", "").strip()
                # Normalize: ensure + prefix for E.164
                if clean_phone and not clean_phone.startswith("+"):
                    clean_phone_with_plus = f"+{clean_phone}"
                else:
                    clean_phone_with_plus = clean_phone
                
                p_rec = db.query(PhoneNumber).filter(
                    (PhoneNumber.phone_number == clean_phone) | 
                    (PhoneNumber.phone_number == clean_phone_with_plus)
                ).first()
                if p_rec:
                    logger.info(f"SIP: Matched phone '{clean_phone}' → workspace={p_rec.workspace_id}, agent={p_rec.agent_id}")
                    return p_rec.workspace_id, p_rec.agent_id

                # Legacy fallback
                workspace = db.query(Workspace).filter(Workspace.inbound_agent_phone == phone_candidate).first()
                if workspace:
                    return workspace.id, None
        finally:
            db.close()
        return None, None

    @staticmethod
    def _resolve_from_participant_metadata(participant):
        try:
            meta = json.loads(participant.metadata)
            workspace_id = meta.get("workspace_id")
            agent_id = meta.get("agent_id")
            call_context = meta.get("call_context")
            return workspace_id, agent_id, call_context, meta
        except:
            return None, None, None, {}
