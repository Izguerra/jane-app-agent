
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load absolute .env
root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=root / ".env")

url = os.getenv("DATABASE_URL")
if not url:
    print("No DATABASE_URL found")
    exit(1)

# Fix postgres:// for sqlalchemy
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        # Get all Telnyx and Twilio numbers with their associated agents
        query = text("SELECT phone_number, friendly_name, provider, agent_id, workspace_id FROM phone_numbers WHERE (provider = 'telnyx' OR provider = 'twilio') AND is_active = True;")
        result = conn.execute(query)
        print("\n--- Active Phone Numbers ---")
        for row in result:
            print(f"Number: {row.phone_number} | Mode: {row.friendly_name} | Agent: {row.agent_id} | Workspace: {row.workspace_id}")
except Exception as e:
    print(f"Error: {e}")
