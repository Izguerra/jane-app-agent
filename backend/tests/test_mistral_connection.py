import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def test_connection():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ MISTRAL_API_KEY not found in environment")
        return

    print(f"🔑 Testing Mistral API connectivity with key: {api_key[:5]}...")
    
    # Models to test
    models = ["mistral-small-latest", "mistral-small", "open-mixtral-8x7b", "mistral-large-latest"]
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.mistral.ai/v1"
    )
    
    for model in models:
        try:
            print(f"Testing model: {model}")
            completion = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print(f"✅ Success with {model}: {completion.choices[0].message.content}")
            return # Stop after first success
            
        except Exception as e:
            print(f"❌ Failed with {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
