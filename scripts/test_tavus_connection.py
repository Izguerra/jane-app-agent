
import sys
import os
import json
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from backend.services.tavus_service import TavusService

def test_tavus_connection():
    print("--- Testing Tavus API Connection ---")
    
    api_key = os.getenv("TAVUS_API_KEY")
    if not api_key:
        print("ERROR: TAVUS_API_KEY not found in environment.")
        return

    print(f"API Key present: {api_key[:5]}...{api_key[-5:]}")
    
    service = TavusService(api_key=api_key)
    
    # 1. List Replicas
    print("\n1. Listing Replicas...")
    replicas = service.list_replicas()
    if not replicas:
        print("WARNING: No replicas found or API failed.")
    else:
        print(f"Found {len(replicas)} replicas.")
        print(f"First Replica: {replicas[0].get('replica_id')} - {replicas[0].get('replica_name')}")
        print(f"Replica Keys: {list(replicas[0].keys())}")

    # 2. List Personas
    print("\n2. Listing Personas...")
    personas = service.list_personas()
    if not personas:
        print("WARNING: No personas found or API failed.")
    else:
        print(f"Found {len(personas)} personas.")
        print(f"First Persona: {personas[0].get('persona_id')} - {personas[0].get('persona_name')}")

    # 3. Match Logic (Mimicking Frontend Fix)
    print("\n3. Testing Valid Replica-Persona Pair...")
    
    target_replica_id = None
    target_persona_id = None
    selected_replica_name = "Unknown"

    if replicas and personas:
        # Search for a replica that has a matching persona
        print("Searching for a valid Replica -> Persona match...")
        for r in replicas:
            rid = r.get('replica_id')
            # Check if any persona points to this replica
            match = next((p for p in personas if p.get('default_replica_id') == rid), None)
            
            if match:
                target_replica_id = rid
                target_persona_id = match.get('persona_id')
                selected_replica_name = r.get('replica_name')
                print(f" -> MATCH FOUND: Replica '{selected_replica_name}' ({rid}) matches Persona '{match.get('persona_name')}' ({target_persona_id})")
                break
        
        if not target_replica_id:
             print("WARNING: No exact match found. Falling back to first available (might fail).")
             target_replica_id = replicas[0].get('replica_id')
             target_persona_id = personas[0].get('persona_id')

        print(f"\n4. Creating Conversation...")
        print(f"   Replica: {target_replica_id}")
        print(f"   Persona: {target_persona_id}")
        
        result = service.create_conversation(
            replica_id=target_replica_id,
            persona_id=target_persona_id,
            name="Manual Test Conversation"
        )
        
        if result:
            print("\nSUCCESS: Conversation Created!")
            print(json.dumps(result, indent=2))
        else:
            print("\nFAILURE: Could not create conversation.")
    else:
        print("\nSKIPPING Conversation Creation (Missing Replicas or Personas)")

if __name__ == "__main__":
    test_tavus_connection()
