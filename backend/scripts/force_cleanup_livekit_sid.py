import os
import asyncio
import httpx
from livekit import api
from dotenv import load_dotenv

async def force_cleanup_by_sid():
    load_dotenv()
    url = os.getenv("LIVEKIT_URL").replace("wss://", "https://")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    # SIDs from the user's dashboard screenshot
    sids = [
        "RM_AuYLzd4PCUfE", # 65 mins, 2 part
        "RM_SwYEwoJL7B5g", # 126 mins, 0 part
        "RM_Gq89zvppyf7T", # 133 mins, 0 part
        "RM_9H2XjFxNid2T", # 169 mins, 0 part
        "RM_Ysx7Z4RBWoGT", # 203 mins, 0 part
        "RM_mm6brgcibYxG", # 663 mins, 0 part
        "RM_HKMe4GQMgyQ6"  # 784 mins, 1 part
    ]
    
    token = api.AccessToken(key, secret) \
        .with_grants(api.VideoGrants(room_admin=True)) \
        .to_jwt()
    
    async with httpx.AsyncClient() as client:
        print(f"Force deleting {len(sids)} rooms by SID...")
        for sid in sids:
            try:
                # RoomService.DeleteRoom can take NAME or SID
                response = await client.post(
                    f"{url}/twirp/livekit.RoomService/DeleteRoom",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"room": sid}
                )
                print(f" - {sid}: Status {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
            except Exception as e:
                print(f"   Exception for {sid}: {e}")

if __name__ == "__main__":
    asyncio.run(force_cleanup_by_sid())
