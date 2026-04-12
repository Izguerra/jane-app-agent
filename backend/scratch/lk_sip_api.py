import asyncio
from livekit import api

async def main():
    lk_api = api.LiveKitAPI("http://localhost:7880", "devkey", "secret")
    print([name for name in dir(lk_api.sip) if not name.startswith('_')])
    await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
