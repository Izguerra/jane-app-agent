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
        Cumulatively merges settings from room and participant metadata.
        """
        workspace_id = None
        agent_id = None
        call_context = None
        settings = {}

        # 1. Room Metadata
        if ctx.room.metadata:
            try:
                room_settings = json.loads(ctx.room.metadata)
                settings.update(room_settings)
                workspace_id = settings.get("workspace_id")
                agent_id = settings.get("agent_id")
                if workspace_id:
                    logger.info(f"Resolved workspace_id={workspace_id} from ROOM metadata")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse room metadata: {e}")

        # 2. Participant Metadata (Always merge, even if workspace_id already found)
        if participant.metadata:
            try:
                p_meta = json.loads(participant.metadata)
                settings.update(p_meta)
                # Update IDs if present in participant metadata (overrides room)
                if p_meta.get("workspace_id"): workspace_id = p_meta.get("workspace_id")
                if p_meta.get("agent_id"): agent_id = p_meta.get("agent_id")
                if p_meta.get("call_context"): call_context = p_meta.get("call_context")
                logger.info("Merged settings from PARTICIPANT metadata")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse participant metadata: {e}")

        # 3. Strategy: Room Name (Fallback for IDs)
        if not workspace_id:
            workspace_id, agent_id, call_context = await VoiceContextResolver._resolve_from_room_name(ctx.room.name)

        # 4. Strategy: SIP Attributes (Fallback for Workspace)
        if not workspace_id:
            workspace_id = await VoiceContextResolver._resolve_from_sip(participant)

        # 5. Full Fallback
        if not workspace_id:
            logger.warning("FALLBACK: No workspace_id resolved. Using default workspace.")
            workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
        
        # Ensure workspace_id and agent_id are in settings for downstream services
        settings["workspace_id"] = workspace_id
        if agent_id:
            settings["agent_id"] = agent_id
        if call_context:
            settings["call_context"] = call_context

        # Final sync from settings to IDs
        agent_id = settings.get("agent_id")
        call_context = settings.get("call_context")

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

            elif "wrk_" in room_name:
                parts = room_name.split("_")
                # Find the part starting with wrk_ (usually the first, but be robust)
                workspace_part = next((p for p in parts if p.startswith("wrk")), None)
                if workspace_part:
                    # Handle both "wrk_" and "wrk" prefixes
                    if workspace_part.startswith("wrk_"):
                        workspace_id = workspace_part
                    elif workspace_part.startswith("wrk"):
                        workspace_id = "wrk_" + workspace_part[3:]
                
                # Check for agent ID in room name
                agent_part = next((p for p in parts if p.startswith("agnt")), None)
                if agent_part:
                    if agent_part.startswith("agnt_"):
                        agent_id = agent_part
                    elif agent_part.startswith("agnt"):
                        agent_id = "agnt_" + agent_part[4:]
                
                logger.info(f"Resolved from DASHBOARD/GENERIC room name: workspace_id={workspace_id}, agent_id={agent_id}")
        except Exception as e:
            logger.error(f"Room name resolution error: {e}")
        finally:
            db.close()
        
        return workspace_id, agent_id, call_context

    @staticmethod
    async def _resolve_from_sip(participant):
        sip_to = participant.attributes.get("sip.callTo") or participant.attributes.get("to")
        sip_from = participant.attributes.get("sip.callFrom") or participant.attributes.get("from")
        
        db = SessionLocal()
        try:
            for phone_candidate in [sip_to, sip_from]:
                if not phone_candidate: continue
                clean_phone = phone_candidate.split("@")[0].replace("sip:", "").strip()
                
                p_rec = db.query(PhoneNumber).filter(
                    (PhoneNumber.phone_number == clean_phone) | 
                    (PhoneNumber.phone_number == f"+{clean_phone}")
                ).first()
                if p_rec: return p_rec.workspace_id

                # Legacy fallback
                workspace = db.query(Workspace).filter(Workspace.inbound_agent_phone == phone_candidate).first()
                if workspace: return workspace.id
        finally:
            db.close()
        return None

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
