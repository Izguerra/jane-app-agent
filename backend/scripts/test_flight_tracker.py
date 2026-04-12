import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.tools.external_tools import ExternalTools

async def run_tests():
    tools = ExternalTools(workspace_id="wrk_000V7dMzXJLzP5mYgdf7FzjA3J")
    
    print("\n--- Testing Single Flight ---")
    res1 = await tools.get_flight_status(flight_number="AC100")
    print(res1)
    
    print("\n--- Testing Route Schedule ---")
    res2 = await tools.get_flight_status(origin="YYZ", destination="JFK")
    print(res2)

if __name__ == "__main__":
    asyncio.run(run_tests())
