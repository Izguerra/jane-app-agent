import asyncio
import os
from backend.tools.external_tools import ExternalTools

async def debug_apis():
    tools = ExternalTools()
    
    print("--- DEBUGGING FLIGHT AC 415 ---")
    res = await tools.get_flight_status(flight_number="AC 415")
    print(f"Result for AC 415: {res}")
    
    print("\n--- DEBUGGING MAPS CN TOWER ---")
    # User case: "How long to CN Tower" (Missing origin)
    # The worker logic usually requires origin.
    # If the Agent doesn't provide it, we expected it to ask.
    # Let's see if Google Maps API works with just a destination? No, origin is required.
    res_map = await tools.get_directions(origin="Toronto Pearson Airport", destination="CN Tower", mode="driving")
    print(f"Result for Map: {res_map}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_apis())
