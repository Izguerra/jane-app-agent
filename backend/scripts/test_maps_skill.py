import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.tools.external_tools import ExternalTools

async def test_distance():
    print("Testing get_directions with postal code L9T0E2 and CN Tower...")
    # Mock workspace_id for lookup
    tools = ExternalTools(workspace_id=None)
    
    # Manually inject key if needed for local test, otherwise it should find it in .env
    # tools.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    res = await tools.get_directions(origin="L9T0E2", destination="CN Tower")
    print(f"\nResult: {res}")
    
    if "The driving directions" in res and "km" in res:
        print("\n✅ Verification Passed: Distance correctly fetched.")
    else:
        print("\n❌ Verification Failed: Result structure incorrect.")

if __name__ == "__main__":
    asyncio.run(test_distance())
