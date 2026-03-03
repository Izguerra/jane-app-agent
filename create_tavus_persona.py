
import asyncio
import os
import json
from dotenv import load_dotenv
from livekit.plugins.tavus.api import TavusAPI

load_dotenv()

async def create_persona():
    api_key = os.getenv("TAVUS_API_KEY")
    if not api_key:
        print("Error: TAVUS_API_KEY not found in .env")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    
    tavus = TavusAPI(api_key=api_key)

    print("Creating 'SupaAgent Universal LiveKit' Persona...")
    
    try:
        # Create persona with explicit Echo Mode and LiveKit Transport
        persona_id = await tavus.create_persona(
            name="SupaAgent Universal LiveKit",
            extra_payload={
                "pipeline_mode": "echo",
                "layers": {
                    "transport": {
                        "transport_type": "livekit"
                    }
                }
            }
        )
        print(f"\nSUCCESS! Persona Created.")
        print(f"Persona ID: {persona_id}")
        print("\nPlease update your settings/code with this ID.")
        
    except Exception as e:
        print(f"Error creating persona: {e}")
    finally:
        await tavus._session.close()

if __name__ == "__main__":
    asyncio.run(create_persona())
