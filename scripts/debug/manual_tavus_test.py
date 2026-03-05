import os
import sys
import logging

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.tavus_service import TavusService
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manual-test")

def test_tavus_flow():
    load_dotenv()
    api_key = os.getenv("TAVUS_API_KEY")
    if not api_key:
        logger.error("TAVUS_API_KEY not found")
        return

    service = TavusService(api_key=api_key)
    
    # 1. List Replicas
    logger.info("--- Listing Replicas ---")
    replicas = service.list_replicas()
    if not replicas:
        logger.error("No replicas found.")
        return
    
    replica_id = replicas[0].get("replica_id")
    logger.info(f"Found Replica: {replica_id} ({replicas[0].get('replica_name')})")

    # 2. List Personas
    logger.info("--- Listing Personas ---")
    personas = service.list_personas()
    persona_id = None
    if personas:
        persona_id = personas[0].get("persona_id")
        logger.info(f"Found Persona: {persona_id} ({personas[0].get('persona_name')})")
    else:
        logger.warning("No personas found. Will rely on default/auto-creation if supported.")

    # 3. Create Conversation
    logger.info("--- Creating Conversation ---")
    # Using dummy token to verify API acceptance
    # conversation_name is passed in payload
    # properties are currently omitted in my updated service, checking if that works
    
    # Note: My updated service signature is: 
    # create_conversation(self, replica_id: str, persona_id: str = None, name: str = "New Conversation")
    
    try:
        response = service.create_conversation(
            replica_id=replica_id,
            persona_id=persona_id,
            name="Manual Debug Conversation"
        )
        
        if response:
            c_id = response.get("conversation_id")
            logger.info(f"\nSUCCESS! Conversation ID: {c_id}")
            logger.info(f"Full Response: {response}")
            return c_id
        else:
            logger.error("Failed to create conversation.")
            
    except Exception as e:
        logger.error(f"Exception during creation: {e}")

if __name__ == "__main__":
    test_tavus_flow()
