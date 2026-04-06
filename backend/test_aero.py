import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

async def main():
    aero_key = os.getenv("AEROAPI_KEY") or os.getenv("FLIGHTAWARE_API_KEY")
    if not aero_key:
        print("NO KEY")
        return
    
    url = f"https://aeroapi.flightaware.com/aeroapi/flights/ACA190/map"
    headers = {"x-apikey": aero_key}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(resp.status)
            if resp.status == 200:
                data = await resp.json()
                print(json.dumps(data, indent=2))
            else:
                print(await resp.text())

if __name__ == "__main__":
    asyncio.run(main())
