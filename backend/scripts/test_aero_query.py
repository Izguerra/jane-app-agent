import asyncio
import os
import sys
import aiohttp
from datetime import datetime, timedelta, timezone

async def test_schedules():
    apikey = "v5GJwXrDuCHkGfV2G4cjmnbkQ2jfjVvD"
    headers = {"x-apikey": apikey}
    
    url_test = f"https://aeroapi.flightaware.com/aeroapi/schedules/2026-04-09/2026-04-11?origin=CYYZ&destination=KJFK" 
    
    async with aiohttp.ClientSession() as session:
        print("Testing schedules with path dates")
        async with session.get(url_test, headers=headers) as req:
            print(req.status, await req.text())
            
if __name__ == "__main__":
    asyncio.run(test_schedules())
