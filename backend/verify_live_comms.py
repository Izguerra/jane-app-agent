
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()

from backend.database import SessionLocal
from backend.models_db import Workspace, Agent
from backend.services.sms_service import send_sms
from backend.services.tavus_service import TavusService
from backend.agent import AgentManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-live-comms")

def print_result(name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name}: {message}")

async def verify_chat(db, workspace_id):
    print(f"\n--- Testing AI Chat (OpenAI) ---")
    try:
        agent = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
        if not agent:
            print_result("AI Chat", False, "No agent found in database")
            return
            
        manager = AgentManager()
        # Call async chat method
        full_response = await manager.chat(
            message="Hello, are you functional?",
            agent_id=agent.id,
            workspace_id=workspace_id,
            team_id="test_team",
            stream=False
        )
            
        if full_response:
            print_result("AI Chat", True, f"Response received: {full_response[:50]}...")
        else:
            print_result("AI Chat", False, "Received empty response")
    except Exception as e:
        print_result("AI Chat", False, str(e))

async def verify_sms_connectivity():
    print(f"\n--- Testing SMS Connectivity (Twilio) ---")
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        print_result("SMS Connectivity", False, "Twilio credentials missing in .env")
        return
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        # Instead of sending a message, list recent messages to verify connectivity
        messages = client.messages.list(limit=1)
        print_result("SMS Connectivity", True, "Successfully authenticated and listed recent messages")
    except Exception as e:
        print_result("SMS Connectivity", False, str(e))

async def verify_tavus():
    print(f"\n--- Testing AI Avatar Connectivity (Tavus) ---")
    tavus_key = os.getenv("TAVUS_API_KEY")
    if not tavus_key:
        print_result("AI Avatar", False, "Tavus API Key missing in .env")
        return
        
    try:
        ts = TavusService()
        replicas = ts.list_replicas()
        if replicas is not None:
             print_result("AI Avatar", True, f"Successfully listed {len(replicas)} replicas")
        else:
             print_result("AI Avatar", False, "Failed to list replicas")
    except Exception as e:
        print_result("AI Avatar", False, str(e))

async def main():
    db = SessionLocal()
    try:
        ws = db.query(Workspace).first()
        if not ws:
            print("No workspaces found in database. Cannot test Chat.")
        else:
            await verify_chat(db, ws.id)
            
        await verify_sms_connectivity()
        await verify_tavus()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
