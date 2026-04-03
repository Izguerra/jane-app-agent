import logging
import os
import sys
from dotenv import load_dotenv

# Path Setup
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test-gemini")

try:
    from livekit.plugins import google as google_plugin
    # Check if google-genai is available for thinking_config
    try:
        from google.genai import types
        has_genai = True
    except ImportError:
        has_genai = False
        print("google-genai NOT FOUND")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        
    if not api_key:
        print("MISSING GOOGLE_API_KEY / GOOGLE_GEMINI_API_KEY")
        sys.exit(1)
        
    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    print("Attempting to initialize RealtimeModel...")
    
    kwargs = {
        "model": "gemini-3.1-flash-live-preview",
        "api_key": api_key,
        "api_version": "v1alpha",
        "instructions": "Test instructions",
        "modalities": ["AUDIO", "TEXT"],
        "voice": "Aoede",
    }
    
    if has_genai:
        kwargs["thinking_config"] = types.ThinkingConfig(include_thoughts=False)
        print("Added thinking_config to kwargs")

    model = google_plugin.realtime.RealtimeModel(**kwargs)
    print("SUCCESS: RealtimeModel initialized")
    print(f"Model object: {model}")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
