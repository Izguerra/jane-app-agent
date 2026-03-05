"""
Seed Email Worker Template
"""
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import WorkerTemplate

def seed_email_worker():
    db = SessionLocal()
    try:
        print("Seeding Email Worker Template...")
        
        # Check if exists
        existing = db.query(WorkerTemplate).filter(WorkerTemplate.slug == "email-worker").first()
        if existing:
            print("Email Worker already exists. Updating...")
            existing.name = "Email Assistant"
            existing.description = "Manages mailbox interactions: checking, searching, summarizing, and drafting replies."
            existing.category = "productivity"
            existing.is_active = True
        else:
            print("Creating new Email Worker template...")
            import uuid
            template = WorkerTemplate(
                id=str(uuid.uuid4()),
                slug="email-worker",
                name="Email Assistant",
                description="Manages mailbox interactions: checking, searching, summarizing, and drafting replies.",
                category="productivity",
                icon="mail", # Assuming an icon field exists or handled by frontend mapping
                is_active=True,
                parameter_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["search", "summarize", "reply"],
                            "description": "The action to perform"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query or topic"
                        },
                        "scope": {
                            "type": "string",
                            "enum": ["today", "week", "unread"],
                            "description": "Time/status scope"
                        }
                    },
                    "required": ["action"]
                }
            )
            db.add(template)
        
        db.commit()
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_email_worker()
