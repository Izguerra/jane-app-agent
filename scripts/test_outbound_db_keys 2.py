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
        # Verify keys are missing from environment
        print("ELEVENLABS_API_KEY in env:", 'ELEVENLABS_API_KEY' in os.environ)
        print("OPENWEATHERMAP_API_KEY in env:", 'OPENWEATHERMAP_API_KEY' in os.environ)
        
        result = await outbound_calling_service.initiate_call(
            workspace_id="wrk_1768318949488",
            to_phone="+14039910411", # Known user test number
            from_phone="+16478006854", # From DB config
            call_intent="test_db_keys",
            call_context={"test": "Verify DB keys work without .env"},
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
