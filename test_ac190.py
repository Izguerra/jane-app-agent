import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from backend.tools.external_tools import ExternalTools

async def test_flight():
    # AC190: Kelowna (YLW) to Toronto (YYZ)
    tools = ExternalTools()
    # Let's see the raw data by modifying how we call or print
    # Since get_flight_status returns a formatted string, I'll temporarily modify it or just print more here
    result = await tools.get_flight_status(flight_number="AC190")
    print("--- Flight Status for AC190 ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_flight())
