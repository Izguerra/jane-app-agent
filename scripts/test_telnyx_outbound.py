import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from backend.database import SessionLocal
from backend.services.outbound_calling_service import outbound_calling_service

async def main():
    db = SessionLocal()
    try:
        print("Initiating outbound call using DB keys...")
        
        result = await outbound_calling_service.initiate_call(
            workspace_id="wrk_1768318949488",
            to_phone="+14039910411", # Known user test number
            from_phone="+18382061295", # The Telnyx DB Number
            call_intent="test_telnyx",
            call_context={"test": "Verify Telnyx Outbound routing works"},
            customer_id=None,
            db=db
        )
        print("Success! Result:", result)
    except Exception as e:
        print("Failed!", e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
