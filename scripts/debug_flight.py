import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def test_flight_status():
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        print("Error: AVIATIONSTACK_API_KEY not found in .env")
        return

    # Test cases
    tests = [
        {"desc": "Flight w/ Space", "params": {"flight_iata": "AC 417"}},
        {"desc": "Flight usually invalid w/ space", "params": {"flight_iata": "AC417"}},
        {"desc": "Route Search", "params": {"dep_iata": "YUL", "arr_iata": "YYZ"}}
    ]

    async with aiohttp.ClientSession() as session:
        for t in tests:
            print(f"\n--- Testing: {t['desc']} ---")
            params = t['params']
            params['access_key'] = api_key
            
            try:
                url = "http://api.aviationstack.com/v1/flights"
                async with session.get(url, params=params) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get('data', [])
                        print(f"Results found: {len(results)}")
                        for i, flight in enumerate(results[:3]): # Show top 3
                            f_iata = flight.get('flight', {}).get('iata')
                            status = flight.get('flight_status')
                            dep = flight.get('departure', {}).get('scheduled')
                            airline = flight.get('airline', {}).get('name')
                            print(f"  {i+1}. {f_iata} ({airline}) - {status} @ {dep}")
                    else:
                        print(f"Error: {await resp.text()}")
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_flight_status())
