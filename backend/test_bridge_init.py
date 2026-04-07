import asyncio
from livekit import rtc
from backend.utils.multimodal_agent import MultimodalAgent
from livekit.agents.voice import VoiceAgent
from livekit.plugins import google, silero

async def test_multimodal_init():
    # Mocking necessary components
    model = google.realtime.RealtimeModel(model="gemini-2.5-flash-native-audio-preview", api_key="fake")
    vad = silero.VAD.load()
    
    # We just want to see if the constructor and start() setup (before awaiting start) work
    print("Initializing MultimodalAgent bridge...")
    
    # Dummy voice agent for the bridge
    voice_agent = VoiceAgent(vad=vad, stt=None, tts=None, llm=model)
    
    bridge = MultimodalAgent(
        model=model,
        vad=vad,
        voice_agent=voice_agent,
        tools=[],
        greeting="Hello!"
    )
    
    print("✅ Bridge initialized successfully.")
    
    # We can't easily test start() without a real room, but we've fixed the signature.
    # The signature fix was: await self._session.start(room, room_options=room_options)
    # in multimodal_agent.py:164
    
if __name__ == "__main__":
    try:
        asyncio.run(test_multimodal_init())
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
