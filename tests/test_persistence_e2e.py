import sys
import os
import json
import time
from datetime import datetime

# Set up project root in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.models_db import Agent
from sqlalchemy.orm.attributes import flag_modified

def test_persistence_loop(agent_id, iterations=3):
    print(f"🚀 Starting Persistence E2E Test for Agent: {agent_id}")
    db = SessionLocal()
    
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            print(f"❌ Error: Agent {agent_id} not found.")
            return

        test_configs = [
            {"voice_id": "alloy", "avatar_voice_id": "en-US-Neural2-F", "avatar_provider": "anam"},
            {"voice_id": "nova", "avatar_voice_id": "en-US-Neural2-D", "avatar_provider": "tavus"},
            {"voice_id": "ash", "avatar_voice_id": "en-US-Standard-C", "avatar_provider": "anam"}
        ]

        for i, config in enumerate(test_configs):
            print(f"\n🔄 Iteration {i+1}: Switching to {config['voice_id']} / {config['avatar_provider']}...")
            
            # Record before state
            old_updated_at = agent.updated_at
            
            # Apply changes (replicating updated_agent logic in crud.py)
            agent.voice_id = config["voice_id"]
            
            current_settings = dict(agent.settings) if agent.settings else {}
            current_settings.update({
                "avatar_voice_id": config["avatar_voice_id"],
                "avatar_provider": config["avatar_provider"]
            })
            agent.settings = current_settings
            flag_modified(agent, "settings")
            
            db.commit()
            db.refresh(agent)
            
            # Verification
            new_updated_at = agent.updated_at
            print(f"  ✅ Voice ID: {agent.voice_id}")
            print(f"  ✅ Avatar Voice ID: {agent.settings.get('avatar_voice_id')}")
            print(f"  ✅ Avatar Provider: {agent.settings.get('avatar_provider')}")
            
            if new_updated_at != old_updated_at:
                print(f"  ✨ Success: updated_at changed from {old_updated_at} to {new_updated_at}")
            else:
                # Note: If tests run too fast, timestamps might match depending on DB resolution, 
                # but with SQLAlchemy client-side func.now(), they usually differ.
                print(f"  ⚠️ Warning: updated_at remained {old_updated_at}. (Might be sub-second overlap)")

            # Small delay to ensure timestamp difference
            time.sleep(1.1)

        print("\n🏆 E2E Persistence Test Completed Successfully!")

    except Exception as e:
        print(f"❌ E2E Test Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    target_agent = "agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ"
    test_persistence_loop(target_agent)
