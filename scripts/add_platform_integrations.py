from backend.database import SessionLocal
from sqlalchemy import text

def add_integrations():
    db = SessionLocal()
    try:
        # Check and add Telnyx
        res = db.execute(text("SELECT id FROM platform_integrations WHERE provider = 'telnyx'")).fetchone()
        if not res:
            db.execute(text("""
                INSERT INTO platform_integrations (id, provider, display_name, description, is_enabled, created_at, updated_at)
                VALUES (gen_random_uuid(), 'telnyx', 'Telnyx', 'Enterprise-grade telephony and messaging integration.', true, now(), now())
            """))
            print("Added Telnyx integration")
        else:
            print("Telnyx integration already exists")

        # Check and add LiveKit
        res = db.execute(text("SELECT id FROM platform_integrations WHERE provider = 'livekit'")).fetchone()
        if not res:
            db.execute(text("""
                INSERT INTO platform_integrations (id, provider, display_name, description, is_enabled, created_at, updated_at)
                VALUES (gen_random_uuid(), 'livekit', 'LiveKit', 'Real-time audio and video infrastructure for agents.', true, now(), now())
            """))
            print("Added LiveKit integration")
        else:
            print("LiveKit integration already exists")

        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_integrations()
