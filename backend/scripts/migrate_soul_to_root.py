import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add the project root to sys.path to allow importing from backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.models_db import Agent

def migrate_stale_settings():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        print(f"Checking {len(agents)} agents for stale settings...")
        
        count = 0
        for agent in agents:
            modified = False
            settings = agent.settings or {}
            
            # Fields that should be at the root, not in settings
            base_fields = {
                "soul": "soul",
                "description": "description",
                "name": "name",
                "is_active": "is_active",
                "voice_id": "voice_id",
                "language": "language",
                "welcome_message": "welcome_message",
                "prompt_template": "prompt_template",
                "allowed_worker_types": "allowed_worker_types"
            }
            
            for settings_key, root_attr in base_fields.items():
                if settings_key in settings:
                    val = settings.pop(settings_key)
                    # Only update root if it's currently empty or different
                    current_root_val = getattr(agent, root_attr)
                    if not current_root_val or current_root_val != val:
                        print(f"Agent {agent.id}: Moving '{settings_key}' from settings to root.")
                        setattr(agent, root_attr, val)
                    else:
                        print(f"Agent {agent.id}: Removing redundant '{settings_key}' from settings.")
                    modified = True
            
            if modified:
                agent.settings = dict(settings)
                db.add(agent)
                count += 1
        
        if count > 0:
            db.commit()
            print(f"Successfully migrated {count} agents.")
        else:
            print("No stale settings found.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_stale_settings()
