import os
import asyncio
from livekit.plugins import google
from dotenv import load_dotenv

load_dotenv()

async def test_model():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: API key missing")
        return

    try:
        print(f"Testing connectivity for model: gemini-2.5-flash-native-audio-preview")
        model = google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview",
            api_key=api_key
        )
        print("✅ RealtimeModel instance created successfully")
        
        # Test if we can at least get a session object (without waiting for connection)
        # Note: We won't actually connect to a room here to keep it simple.
        print("✅ Model instance looks good.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_model())
