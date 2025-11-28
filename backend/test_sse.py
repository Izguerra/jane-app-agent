#!/usr/bin/env python3
import asyncio
import aiohttp

async def test_sse():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:3000/api/agent/settings/stream') as resp:
            print(f"Status: {resp.status}")
            print(f"Headers: {resp.headers}")
            async for line in resp.content:
                print(f"Received: {line.decode()}")

if __name__ == "__main__":
    asyncio.run(test_sse())
