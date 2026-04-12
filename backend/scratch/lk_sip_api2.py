import asyncio
from livekit import api
import sys

async def main():
    try:
        lk_api = api.LiveKitAPI("http://localhost:7880", "devkey", "secret")
        # print docstrings
        print(lk_api.sip.list_sip_inbound_trunk.__doc__)
        print(lk_api.sip.update_sip_inbound_trunk.__doc__)
        await lk_api.aclose()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
