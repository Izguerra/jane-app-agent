import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

load_dotenv()

from backend.database import SessionLocal
from backend.services.outbound_calling_service import outbound_calling_service

async def main():
    db = SessionLocal()
    try:
        # Use user's known number from logs
        target_number = "+14167865786" 
        from_number = "+18382061295" # The Telnyx number
        
        print(f"--- TRIGGERING OUTBOUND E2E TEST ---")
        print(f"Target: {target_number}")
        print(f"From: {from_number}")
        
        workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
        agent_id = "agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ"
        
        print(f"Using Workspace ID: {workspace_id}")
        print(f"Using Agent ID: {agent_id}")
        
        result = await outbound_calling_service.initiate_call(
            workspace_id=workspace_id,
            to_phone=target_number,
            from_phone=from_number,
            call_intent="e2e_outbound_verification",
            call_context={"message": "This is an automated E2E test from Antigravity."},
            customer_id=None,
            agent_id=agent_id,
            db=db
        )
        print("\nAPI Response Success! Call initiation triggered.")
        print("Result:", result)
        print("\nNEXT STEPS:")
        print("1. Wait for your phone to ring.")
        print("2. Answer and listen for the agent greeting.")
        print("3. Check backend.log and voice_agent.log for SIP/LiveKit events.")
        
    except Exception as e:
        import traceback
        print("\nE2E TRIGGER FAILED!")
        print("Error:", e)
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
