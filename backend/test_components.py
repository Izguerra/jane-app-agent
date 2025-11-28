import os
from dotenv import load_dotenv
from livekit.plugins import openai, deepgram, silero
import asyncio

load_dotenv()

async def test_components():
    print("Testing component initialization...")
    
    try:
        print("Testing VAD load...")
        vad = silero.VAD.load()
        print("VAD loaded successfully")
    except Exception as e:
        print(f"VAD failed: {e}")

    try:
        print("Testing OpenAI LLM...")
        llm = openai.LLM()
        print("OpenAI LLM initialized")
    except Exception as e:
        print(f"OpenAI LLM failed: {e}")

    try:
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        print(f"Testing OpenAI TTS with voices: {voices}")
        
        for voice in voices:
            print(f"Testing voice: {voice}")
            tts = openai.TTS(voice=voice)
            text = f"Hello, this is a test of the {voice} voice."
            async for _ in tts.synthesize(text):
                pass
            print(f"Voice {voice} working")
            
        print("All OpenAI TTS voices verified")
    except Exception as e:
        print(f"OpenAI TTS failed: {e}")

    try:
        print("Testing Deepgram STT...")
        stt = deepgram.STT()
        print("Deepgram STT initialized")
    except Exception as e:
        print(f"Deepgram STT failed: {e}")

    try:
        from livekit.agents import llm
        from agent_tools import AgentTools
        print("Testing AgentTools loading...")
        tools = AgentTools()
        function_tools = llm.find_function_tools(tools)
        print(f"Found {len(function_tools)} tools")
        for t in function_tools:
            print(f"Tool: {t}")
            if hasattr(t, '__livekit_tool_info'):
                info = getattr(t, '__livekit_tool_info')
                print(f"  Info: name={info.name}, description={info.description}")
    except Exception as e:
        print(f"AgentTools loading failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_components())
