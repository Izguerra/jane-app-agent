import asyncio
import os
import sys
import traceback

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.tools.external_tools import ExternalTools

async def debug_aero():
    print("🚀 Debugging AeroAPI...")
    tools = ExternalTools(workspace_id=None)
    
    try:
        res = await tools.get_flight_status(flight_number="AC100")
        print(f"\nResult: {res}")
    except Exception:
        print("\n❌ Caught Exception in Test Script:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_aero())
