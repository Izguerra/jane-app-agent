"""
LiveKit SIP Outbound Calling Service

Uses LiveKit's CreateSIPParticipant API to make outbound calls directly,
bypassing Twilio and Asterisk for outbound flow.
"""

import json
import os
import uuid
import logging
from livekit import api
from backend.routers.voice import validate_room_name
from backend.database import SessionLocal, generate_comm_id
from backend.models_db import Communication, Workspace
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class LiveKitOutboundService:
    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.livekit_url = os.getenv("LIVEKIT_URL")
        
        if not all([self.api_key, self.api_secret, self.livekit_url]):
            raise ValueError("LiveKit credentials not configured")
    
    async def initiate_outbound_call(
        self,
        workspace_id: str,
        to_phone: str,
        call_intent: str,
        call_context: dict = None,
        customer_id: str = None,
        agent_id: str = None,
        db = None
    ):
        """
        Initiate an outbound call using LiveKit SIP.
        
        Args:
            workspace_id: Workspace ID
            to_phone: Phone number to call (E.164 format)
            call_intent: Purpose of call (e.g., 'appointment_reminder')
            call_context: Additional context for the call
            customer_id: Optional customer ID
            agent_id: Optional agent ID
            db: Database session
        
        Returns:
            dict with communication_id, room_name, and status
        """
        
        # Create communication record
        communication_id = generate_comm_id()
        room_name = f"outbound-{communication_id or str(uuid.uuid4())[:8]}"
        
        # Validation
        if not validate_room_name(room_name):
            logger.error(f"SECURITY ALERT: Rejected malformed room name in LiveKitOutboundService: {room_name}")
            return None
            
        try:
        # Ensure phone number is in E.164 format
        if not to_phone.startswith('+'):
            to_phone = f"+{to_phone}"
        
        # Create LiveKit API client
        lkapi = api.LiveKitAPI(
            self.livekit_url.replace('wss://', 'https://').replace('ws://', 'http://'),
            self.api_key,
            self.api_secret
        )
        
        try:
            # Create room first
            room = await lkapi.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=60,  # 1 minute (reduced from 5m to prevent leaks)
                    max_participants=2
                )
            )
            
            print(f"Created LiveKit room: {room.name}")
            
            # Create SIP participant (this initiates the outbound call)
            import json
            
            metadata = {
                "communication_id": communication_id,
                "workspace_id": workspace_id,
                "call_intent": call_intent,
                "call_context": call_context or {},
                "customer_id": customer_id,
                "agent_id": agent_id
            }
            
            print(f"Creating SIP participant with:")
            print(f"  - Trunk ID: {os.getenv('LIVEKIT_SIP_TRUNK_ID')}")
            print(f"  - Call to: {to_phone}")
            print(f"  - Room: {room_name}")
            
            sip_participant = await lkapi.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=os.getenv("LIVEKIT_SIP_TRUNK_ID"),
                    sip_call_to=to_phone,
                    room_name=room_name,
                    participant_identity=f"phone-{communication_id}",
                    participant_name=f"Customer {to_phone}",
                    participant_metadata=json.dumps(metadata),  # Must be JSON string
                    play_ringtone=True  # Play ringtone while connecting
                )
            )
            
            print(f"✅ Created SIP participant: {sip_participant.participant_id}")
            print(f"   Participant identity: {sip_participant.participant_identity}")
            print(f"   SIP Call ID: {sip_participant.sip_call_id if hasattr(sip_participant, 'sip_call_id') else 'N/A'}")
            
            # Create communication record in database
            if db:
                communication = Communication(
                    id=communication_id,
                    workspace_id=workspace_id,
                    customer_id=customer_id,
                    type="call",
                    direction="outbound",
                    channel="phone_call",
                    user_identifier=to_phone,
                    status="initiated",
                    call_intent=call_intent,
                    call_context=call_context,
                    started_at=datetime.now(timezone.utc),
                    metadata={
                        "room_name": room_name,
                        "sip_participant_id": sip_participant.participant_id,
                        "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID")
                    }
                )
                db.add(communication)
                db.commit()
                db.refresh(communication)
            
            await lkapi.aclose()
            
            return {
                "communication_id": communication_id,
                "room_name": room_name,
                "sip_participant_id": sip_participant.participant_id,
                "status": "initiated",
                "to": to_phone
            }
            
        except Exception as e:
            print(f"Error creating SIP participant: {e}")
            await lkapi.aclose()
            raise Exception(f"Failed to initiate outbound call: {str(e)}")


# Singleton instance
livekit_outbound_service = LiveKitOutboundService()
