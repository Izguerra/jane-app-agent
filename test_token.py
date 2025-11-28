import os
from livekit import api
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LIVEKIT_API_KEY")
api_secret = os.getenv("LIVEKIT_API_SECRET")

print(f"Key: {api_key}")
print(f"Secret: {api_secret}")

try:
    grant = api.VideoGrants(room_join=True, room="test-room")
    token = api.AccessToken(api_key, api_secret).with_grants(grant).with_identity("user-1").with_name("user-1")
    print(f"Token: {token.to_jwt()}")
except Exception as e:
    print(f"Error: {e}")
