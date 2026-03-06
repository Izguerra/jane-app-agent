"""
Outbound Calling Service

Handles initiating outbound calls via Twilio and LiveKit.
"""
from typing import Optional, Dict, Any
import os
from twilio.rest import Client
from backend.database import generate_comm_id
from backend.models_db import Communication, Customer, Appointment, Deal
from sqlalchemy.orm import Session
from datetime import datetime


class OutboundCallingService:
    def __init__(self):
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.livekit_url = os.getenv("LIVEKIT_URL")
        
        if self.twilio_account_sid and self.twilio_auth_token:
            self.client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.client = None
    
    async def initiate_call(
        self,
        workspace_id: str,
        to_phone: str,
        from_phone: Optional[str] = None,
        call_intent: str = "general",
        call_context: Optional[Dict[str, Any]] = None,
        customer_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        campaign_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        provider: str = "auto",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call via Twilio → LiveKit
        
        Args:
            workspace_id: Workspace ID
            to_phone: Phone number to call (E.164 format)
            from_phone: Twilio phone number to use (optional, uses default if not provided)
            call_intent: Intent of the call (appointment_reminder, deal_follow_up, lead_qualification)
            call_context: Context data (appointment details, deal info, etc.)
            customer_id: Customer ID if applicable
            campaign_id: Campaign ID if applicable
            campaign_name: Campaign name if applicable
            agent_id: Agent ID to use for the call
            db: Database session
        
        Returns:
            Dict with call details including communication_id and twilio_call_sid
        """
        # Auto-detect provider from workspace's phone numbers if not explicitly set
        if provider == "auto":
            try:
                from backend.database import SessionLocal
                from backend.models_db import PhoneNumber, Workspace
                _db = db or SessionLocal()
                
                # 1. Try current workspace
                tel_num = _db.query(PhoneNumber).filter(
                    PhoneNumber.workspace_id == workspace_id,
                    PhoneNumber.provider == "telnyx",
                    PhoneNumber.is_active == True
                ).first()
                
                # 2. If not found, try any workspace in the same team
                if not tel_num:
                    ws = _db.query(Workspace).filter(Workspace.id == workspace_id).first()
                    if ws:
                        # Find all workspaces in the same team
                        team_workspaces = _db.query(Workspace.id).filter(Workspace.team_id == ws.team_id).all()
                        team_ws_ids = [w[0] for w in team_workspaces]
                        
                        tel_num = _db.query(PhoneNumber).filter(
                            PhoneNumber.workspace_id.in_(team_ws_ids),
                            PhoneNumber.provider == "telnyx",
                            PhoneNumber.is_active == True
                        ).first()
                
                if tel_num:
                    provider = "telnyx"
                    from_phone = tel_num.phone_number
                    print(f"DEBUG: Auto-detected Telnyx provider for team/workspace, from_phone={from_phone}")
                else:
                    provider = "twilio"
                    print(f"DEBUG: No Telnyx number found for workspace {workspace_id} or its team, defaulting to Twilio")
                
                if not db:
                    _db.close()
            except Exception as e:
                print(f"WARNING: Provider auto-detect failed ({e}), defaulting to twilio")
                provider = "twilio"
        
        if provider == "twilio":
            if not self.client:
                raise Exception("Twilio client not configured")
        elif provider == "telnyx":
            telnyx_api_key = os.getenv("TELNYX_API_KEY")
            if not telnyx_api_key:
                raise Exception("Telnyx API Key not configured")
            import telnyx
            telnyx.api_key = telnyx_api_key
        
        # Use default phone number if not provided
        if not from_phone:
            from_phone = self.twilio_phone_number
        
        # Create communication record
        communication_id = generate_comm_id()
        
        # Generate unique room name for this call
        # Use 'outbound_' prefix so Asterisk can route to correct context
        room_name = f"outbound_{communication_id}"
        
        # Encode call context in LiveKit room metadata
        room_metadata = {
            "communication_id": communication_id,
            "workspace_id": workspace_id,
            "call_intent": call_intent,
            "call_context": call_context or {},
            "customer_id": customer_id,
            "agent_id": agent_id
        }
        
        # Build TwiML to connect to LiveKit
        # The TwiML URL should point to your backend endpoint that returns the LiveKit connection TwiML
        twiml_url = f"{os.getenv('BACKEND_URL')}/api/voice/outbound-twiml?room={room_name}&metadata={self._encode_metadata(room_metadata)}"
        
        print(f"DEBUG: TwiML URL being sent to Twilio: {twiml_url}")
        
        try:
            # ---------------------------------------------------------
            # PRE-CREATE ROOM to ensure Agent is dispatched and ready
            # ---------------------------------------------------------
            try:
                from livekit import api
                import json
                
                lk_api_key = os.getenv("LIVEKIT_API_KEY")
                lk_api_secret = os.getenv("LIVEKIT_API_SECRET")
                lk_url = os.getenv("LIVEKIT_URL")
                
                if lk_api_key and lk_api_secret and lk_url:
                    print(f"DEBUG: Pre-creating room {room_name} for agent dispatch")
                    lkapi = api.LiveKitAPI(lk_url, lk_api_key, lk_api_secret)
                    
                    # Create room with explicit dispatch
                    # This ensures that when Asterisk connects via SIP, the agent is already being dispatched
                    # or is ready to join.
                    await lkapi.room.create_room(api.CreateRoomRequest(
                        name=room_name,
                        empty_timeout=60,
                        max_participants=2,
                        agents=[
                            api.RoomAgentDispatch(agent_name="supaagent-voice-agent-v2")
                        ],
                        metadata=json.dumps(dict(room_metadata))
                    ))
                    await lkapi.aclose()
                    print(f"DEBUG: Pre-created room {room_name} successfully")
            except Exception as e:
                print(f"WARNING: Failed to pre-create room (continuing anyway): {e}")

            # Initiate call via selected provider
            call_sid = None
            if provider == "twilio":
                call = self.client.calls.create(
                    to=to_phone,
                    from_=from_phone,
                    url=twiml_url,
                    status_callback=f"{os.getenv('BACKEND_URL')}/api/voice/status-callback",
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed']
                )
                call_sid = call.sid
            elif provider == "telnyx":
                # Reverting to Call Control as TeXML was 404ing
                from backend.services.telnyx_service import TelnyxService
                telnyx_svc = TelnyxService()
                connection_id = os.getenv("TELNYX_CONNECTION_ID")
                
                print(f"DEBUG: Initiating Telnyx Call Control call from {from_phone} to {to_phone} using Connection ID: {connection_id}")
                
                if connection_id:
                    if not telnyx_svc.client:
                        raise Exception("Telnyx client not initialized")
                    call_result = telnyx_svc.client.calls.dial(
                        connection_id=connection_id,
                        to=to_phone,
                        from_=from_phone
                    )
                    call_sid = call_result.data.call_control_id
                else:
                    print("WARNING: No TELNYX_CONNECTION_ID configured.")
                    call_sid = f"err_{communication_id}"
            
            # Create communication record in database
            if db:
                communication = Communication(
                    id=communication_id,
                    workspace_id=workspace_id,
                    type="call",
                    direction="outbound",
                    status="initiated",
                    user_identifier=to_phone,
                    channel="phone_call",
                    agent_id=agent_id,
                    call_intent=call_intent,
                    call_context=call_context,
                    customer_id=customer_id,
                    twilio_call_sid=call_sid if provider == "twilio" else None,
                    telnyx_call_id=call_sid if provider == "telnyx" else None,
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    started_at=datetime.utcnow()
                )
                db.add(communication)
                db.commit()
            
            return {
                "success": True,
                "communication_id": communication_id,
                "call_id": call_sid,
                "status": "initiated",
                "to": to_phone,
                "from": from_phone,
                "provider": provider
            }
        
        except Exception as e:
            # Log failed call attempt
            if db:
                communication = Communication(
                    id=communication_id,
                    workspace_id=workspace_id,
                    type="call",
                    direction="outbound",
                    status="failed",
                    user_identifier=to_phone,
                    channel="phone_call",
                    agent_id=agent_id,
                    call_intent=call_intent,
                    call_context=call_context,
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    started_at=datetime.utcnow(),
                    ended_at=datetime.utcnow()
                )
                db.add(communication)
                db.commit()
            
            raise Exception(f"Failed to initiate call: {str(e)}")
    
    def _encode_metadata(self, metadata: Dict[str, Any]) -> str:
        """Encode metadata for URL parameter"""
        import json
        import urllib.parse
        return urllib.parse.quote(json.dumps(metadata))


# Singleton instance
outbound_calling_service = OutboundCallingService()
