import os
import asyncio
from livekit.plugins import google as google_plugin

async def test_gemini():
    gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not gemini_key:
        print("No GOOGLE_GEMINI_API_KEY")
        return
        
    print("Testing gemini-3-flash-preview initialization...")
    try:
        llm_instance = google_plugin.LLM(
            model="gemini-3-flash-preview",
            api_key=gemini_key,
            temperature=0.7
        )
        print("Initialization successful.")
        print("Test complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
