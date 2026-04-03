import asyncio
import os
from backend.tools.external_tools import ExternalTools

async def debug_apis():
    tools = ExternalTools()
    
    print("\n--- TEST 1: Digits Only (Should Fail and ask for info) ---")
    res1 = await tools.get_flight_status(flight_number="190")
    print(f"Result: {res1}")
    
    print("\n--- TEST 2: Airline Name + Digits (Should Merge to AC190) ---")
    res2 = await tools.get_flight_status(flight_number="190", airline="Air Canada")
    print(f"Result: {res2}")
    
    print("\n--- TEST 3: Specific Flight with known Delay (AC 190) ---")
    # This will test the new delay comparison logic as well
    res3 = await tools.get_flight_status(flight_number="AC 190")
    print(f"Result: {res3}")

    print("\n--- TEST 4: AC 1902 (YYJ -> YYZ) ---")
    res4 = await tools.get_flight_status(flight_number="AC 1902", origin="YYJ", destination="YYZ")
    print(f"Result: {res4}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_apis())
