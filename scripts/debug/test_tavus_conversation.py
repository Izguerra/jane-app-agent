import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.tavus_service import TavusService
from dotenv import load_dotenv

load_dotenv()

async def test_create_conversation():
    print("Initializing Tavus Service...")
    tavus = TavusService()
    
    # Use a knwon replica ID or let it pick default
    # If no default, we might need to list replicas first
    print("Listing Replicas to find a valid one...")
    replicas = tavus.list_replicas()
    if not replicas:
        print("ERROR: No replicas found!")
        return

    replica_id = replicas[0].get("replica_id")
    print(f"Using Replica ID: {replica_id}")

    print("Creating Conversation...")
    try:
        # We need a proper callback URL and other params usually, but let's try minimal
        # The service method signature: create_conversation(self, replica_id: str, persona_id: str = None, callback_url: str = None, conversation_name: str = None)
        
        # We also need a persona ID if possible, let's list them
        print("Listing Personas...")
        personas = tavus.list_personas()
        persona_id = None
        if personas:
            persona_id = personas[0].get("persona_id")
            print(f"Using Persona ID: {persona_id}")
            
        result = tavus.create_conversation(
            replica_id=replica_id,
            persona_id=persona_id,
            name="Debug Test Conversation"
        )
        
        print("\nSUCCESS!")
        print(f"Conversation ID: {result.get('conversation_id')}")
        print(f"Full Result: {result}")
        
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_conversation())
