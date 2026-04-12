import os
import uuid
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from livekit import api

from backend.database import SessionLocal, generate_phone_id
from backend.models_db import PhoneNumber
from backend.services.telnyx_service import TelnyxService

class TelephonyProvisioningService:
    def __init__(self, db: Session):
        self.db = db
        self.telnyx_api_key = os.getenv("TELNYX_API_KEY")
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.sip_connection_id = os.getenv("TELNYX_SIP_CONNECTION_ID")
        self.inbound_trunk_id = os.getenv("LIVEKIT_SIP_INBOUND_TRUNK_ID")
        
        if not all([self.telnyx_api_key, self.livekit_url, self.livekit_api_key, self.livekit_api_secret]):
            raise ValueError("Missing essential telephony credentials.")

    def get_livekit_api(self):
        return api.LiveKitAPI(
            url=self.livekit_url,
            api_key=self.livekit_api_key,
            api_secret=self.livekit_api_secret
        )

    async def provision_phone_number(
        self,
        workspace_id: str,
        phone_number: str = None,
        country_code: str = "US",
        area_code: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> PhoneNumber:
        
        telnyx_service = TelnyxService(workspace_id=workspace_id)
        
        # 1. Search if phone_number is not provided
        selected_number = phone_number
        if not selected_number:
            results = telnyx_service.search_phone_numbers(
                country_code=country_code,
                area_code=area_code,
                limit=1,
                features=["voice", "sms"]
            )
            if not results:
                raise HTTPException(status_code=400, detail="No numbers available for the given area code.")
            selected_number = results[0]["phone_number"]

        # 2. Purchase the number
        order = telnyx_service.purchase_phone_number(
            phone_number=selected_number,
            workspace_id=workspace_id
        )
        telnyx_phone_id = order.get("id")

        if not telnyx_phone_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve Telnyx Phone ID after purchase")

        # 3. Assign to Telnyx SIP Connection
        if not self.sip_connection_id:
             print("Warning: TELNYX_SIP_CONNECTION_ID not set, skipping Telnyx Connection Assignment")
        else:
             telnyx_service.configure_voice_connection(telnyx_phone_id, self.sip_connection_id)

        # 4. Add number to LiveKit Trunk
        if self.inbound_trunk_id:
            await self._add_number_to_livekit_trunk(selected_number)
        else:
             print("Warning: LIVEKIT_SIP_INBOUND_TRUNK_ID not set, skipping LiveKit trunk update")

        # 5. Save to Database
        db_number = PhoneNumber(
            id=generate_phone_id(),
            workspace_id=workspace_id,
            phone_number=selected_number,
            friendly_name=selected_number,
            telnyx_id=telnyx_phone_id,
            provider="telnyx",
            voice_enabled=True,
            sms_enabled=True,
            monthly_cost=200, # Telnyx default usually
            country_code=country_code,
            agent_id=agent_id
        )
        
        self.db.add(db_number)
        self.db.commit()
        self.db.refresh(db_number)

        return db_number

    async def _add_number_to_livekit_trunk(self, phone_number: str):
        lk_api = self.get_livekit_api()
        try:
            # We don't have a direct 'get' by ID, but we can list and find
            # or try passing the Trunk ID into an update call if the SDK supports incremental updates. 
            # Looking at LiveKit Python SDK, we usually list and replace entirely.
            
            req = api.ListSIPInboundTrunkRequest(trunk_id=[self.inbound_trunk_id])
            res = await lk_api.sip.list_sip_inbound_trunk(req)
            if not res.items:
                raise Exception("LiveKit trunk not found")
                
            trunk_info = res.items[0]
            existing_numbers = list(trunk_info.numbers)
            
            # format matching provider (strip plus maybe? Wait, LiveKit usually wants E164 with plus for telnyx)
            # ensure standard format
            if phone_number not in existing_numbers:
                existing_numbers.append(phone_number)
            
            # update trunk
            update_req = api.UpdateSIPInboundTrunkRequest(
                trunk_id=self.inbound_trunk_id,
                name=trunk_info.name,
                numbers=existing_numbers,
                allowed_addresses=trunk_info.allowed_addresses,
                allowed_numbers=trunk_info.allowed_numbers
            )
            # Use update endpoint depending on available sdk versions
            try:
                await lk_api.sip.update_sip_inbound_trunk(update_req)
            except AttributeError:
                 # fallback for versions renaming
                 await lk_api.sip.update_inbound_trunk(update_req)

        except Exception as e:
            print(f"Failed to update LiveKit trunk: {e}")
        finally:
            await lk_api.aclose()

    async def _remove_number_from_livekit_trunk(self, phone_number: str):
        if not self.inbound_trunk_id:
             return
        lk_api = self.get_livekit_api()
        try:
            req = api.ListSIPInboundTrunkRequest(trunk_id=[self.inbound_trunk_id])
            res = await lk_api.sip.list_sip_inbound_trunk(req)
            if not res.items:
                 return
                 
            trunk_info = res.items[0]
            existing_numbers = list(trunk_info.numbers)
            
            if phone_number in existing_numbers:
                 existing_numbers.remove(phone_number)
                 update_req = api.UpdateSIPInboundTrunkRequest(
                     trunk_id=self.inbound_trunk_id,
                     name=trunk_info.name,
                     numbers=existing_numbers,
                     allowed_addresses=trunk_info.allowed_addresses,
                     allowed_numbers=trunk_info.allowed_numbers
                 )
                 try:
                    await lk_api.sip.update_sip_inbound_trunk(update_req)
                 except AttributeError:
                    await lk_api.sip.update_inbound_trunk(update_req)
        except Exception as e:
            print(f"Failed to remove number from LiveKit trunk: {e}")
        finally:
            await lk_api.aclose()


    async def deprovision_phone_number(self, phone_id: str):
        number_rec = self.db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
        if not number_rec:
            raise HTTPException(status_code=404, detail="Phone number not found")
        
        # 1. Release from Telnyx
        if number_rec.provider == "telnyx" and number_rec.telnyx_id:
             telnyx_service = TelnyxService(workspace_id=number_rec.workspace_id)
             telnyx_service.release_phone_number(number_rec.telnyx_id)

        # 2. Remove from LiveKit
        if number_rec.phone_number:
            await self._remove_number_from_livekit_trunk(number_rec.phone_number)

        # 3. Delete from DB
        self.db.delete(number_rec)
        self.db.commit()

    def reassign_phone_number(self, phone_id: str, new_agent_id: Optional[str] = None):
        number_rec = self.db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
        if not number_rec:
            raise HTTPException(status_code=404, detail="Phone number not found")
        
        number_rec.agent_id = new_agent_id
        self.db.commit()
        return number_rec
