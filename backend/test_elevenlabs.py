try:
    from livekit.plugins import elevenlabs
    print("Import successful")
    try:
        tts = elevenlabs.TTS(voice=elevenlabs.Voice(id="rachel", name="", category="premade"))
        print("Instantiation successful")
    except Exception as e:
        print(f"Instantiation failed: {e}")
except ImportError as e:
    print(f"Import failed: {e}")




