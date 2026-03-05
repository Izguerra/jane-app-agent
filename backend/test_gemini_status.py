import os
import asyncio
from dotenv import load_dotenv
from livekit.agents import llm

load_dotenv()

async def test_gemini():
    print("Initializing Gemini LLM...")
    try:
        from livekit.plugins import google
        # Explicit check for key
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not key:
            print("ERROR: No Google API Key found in .env")
            return

        agent_llm = google.LLM(
            model="gemini-2.0-flash-exp", # Trying a more standard model name if preview is unstable
            api_key=key
        )
        
        ctx = llm.ChatContext().append(role="user", text="Hello, are you online?")
        
        print("Sending request to Gemini...")
        stream = agent_llm.chat(chat_ctx=ctx)
        
        async for chunk in stream:
            if chunk.delta.content:
                print(f"Response: {chunk.delta.content}")
                break
        print("Success!")
                
    except Exception as e:
        print(f"\nCaught Exception: {type(e).__name__}: {e}")
        # Check if it is a 503 (ServerError) or 429 (Quota)
        if hasattr(e, 'status_code'):
             print(f"Status Code: {e.status_code}")
             if e.status_code == 429:
                 print("Result: You have likely run out of credits/quota.")
             elif e.status_code == 503:
                 print("Result: Gemini is currently overloaded or down (503 Service Unavailable).")
        elif "503" in str(e):
             print("Result: Gemini is currently overloaded or down (503 Service Unavailable).")
        elif "429" in str(e):
             print("Result: You have likely run out of credits/quota.")

if __name__ == "__main__":
    asyncio.run(test_gemini())
