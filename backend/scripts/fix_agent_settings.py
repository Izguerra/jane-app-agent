import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
     DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def fix_agent_settings(agent_id, new_instance_id):
    with engine.connect() as conn:
        print(f"Checking agent {agent_id}...")
        result = conn.execute(text("SELECT settings FROM agents WHERE id = :id"), {"id": agent_id}).fetchone()
        
        if not result:
            print("Agent not found.")
            return

        settings = result[0] or {}
        print(f"Current Settings: {settings}")
        
        current_id = settings.get("open_claw_instance_id") or settings.get("openClawInstanceId")
        print(f"Current Instance ID: {current_id}")
        
        if current_id != new_instance_id:
            print(f"Updating to {new_instance_id}...")
            settings["open_claw_instance_id"] = new_instance_id
            settings["openClawInstanceId"] = new_instance_id # Set both for safety
            
            conn.execute(
                text("UPDATE agents SET settings = :settings WHERE id = :id"),
                {"settings": json.dumps(settings), "id": agent_id}
            )
            conn.commit()
            print("Updated successfully.")
        else:
            print("Already up to date.")

if __name__ == "__main__":
    # Get the latest active instance from DB
    with engine.connect() as conn:
        instance = conn.execute(text("SELECT id FROM worker_instances WHERE worker_type='openclaw' AND status='active' ORDER BY updated_at DESC LIMIT 1")).fetchone()
        if instance:
            new_id = instance[0]
            print(f"Found active instance: {new_id}")
            fix_agent_settings("agnt_000VA6fCM7ooHx7VALTwm40ed8", new_id)
        else:
            print("No active OpenClaw instance found!")
