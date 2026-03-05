import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_tavus():
    try:
        from livekit.plugins.tavus import api
        tavus_api = api.TavusAPI(api_key=os.getenv("TAVUS_API_KEY"))
        print("Creating conversation...")
        res = await tavus_api.create_conversation(replica_id="r6ae5b6efc9d")
        print(f"Result: {res}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tavus())
