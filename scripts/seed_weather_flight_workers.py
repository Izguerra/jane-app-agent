from sqlalchemy import text
from backend.database import SessionLocal
import uuid
import json

def seed_new_workers():
    db = SessionLocal()
    try:
        workers = [
            {
                "name": "Weather Worker",
                "slug": "weather-worker",
                "description": "Checks weather conditions. REQUIRED: Ask for Location if not provided.",
                "category": "utility",
                "default_instructions": "You are a weather agent. Use the weather tool to find current conditions for the specific location.",
                "parameter_schema": json.dumps({
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City and Country/State (REQUIRED)"}
                    },
                    "required": ["location"]
                }),
                "icon": "cloud",
                "color": "sky",
                "is_active": True,
                "is_system": True
            },
            {
                "name": "Flight Tracker",
                "slug": "flight-tracker",
                "description": "Tracks flight status. REQUIRED: Ask for Flight Number OR Origin/Destination.",
                "category": "utility",
                "default_instructions": "You are a flight tracking agent. Use the flight status tool to find flight info.",
                "parameter_schema": json.dumps({
                    "type": "object",
                    "properties": {
                        "flight_number": {"type": "string", "description": "Flight IATA code (e.g. AA123). Preferable."},
                        "origin": {"type": "string", "description": "Departure Airport (e.g. YYZ)"},
                        "destination": {"type": "string", "description": "Arrival Airport (e.g. LHR)"},
                        "airline": {"type": "string", "description": "Airline Code (e.g. AC)"}
                    },
                    "required": []
                }),
                "icon": "plane",
                "color": "blue",
                "is_active": True,
                "is_system": True
            },
            {
                "name": "Navigation Assistant",
                "slug": "map-worker",
                "description": "Calculates routes/traffic. REQUIRED: Ask for Origin and Destination if not provided.",
                "category": "utility",
                "default_instructions": "You are a navigation assistant. Use Google Maps to find the best route.",
                "parameter_schema": json.dumps({
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Starting location (REQUIRED)"},
                        "destination": {"type": "string", "description": "Destination (REQUIRED)"}
                    },
                    "required": ["origin", "destination"]
                }),
                "icon": "map",
                "color": "emerald",
                "is_active": True,
                "is_system": True
            },
            {
                "name": "Translation Specialist",
                "slug": "translation-localization",
                "description": "Translates documents, emails, and long-form content accurately.",
                "category": "content",
                "default_instructions": "You are an expert translator. Translate the provided text.",
                "parameter_schema": json.dumps({
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to translate", "format": "textarea"},
                        "target_language": {"type": "string", "description": "Target Language (e.g. Spanish, French)"},
                        "context": {"type": "string", "description": "Context (e.g. Formal, Casual, Legal)"}
                    },
                    "required": ["text", "target_language"]
                }),
                "icon": "languages",
                "color": "teal",
                "is_active": True,
                "is_system": True
            }
        ]

        print("Seeding new workers (Raw SQL)...")
        for w in workers:
            # Check exist
            check_sql = text("SELECT id FROM worker_templates WHERE slug = :slug")
            result = db.execute(check_sql, {"slug": w["slug"]}).fetchone()
            
            if result:
                print(f"Updating {w['name']}...")
                update_sql = text("""
                    UPDATE worker_templates 
                    SET name=:name, description=:description, category=:category, 
                        default_instructions=:default_instructions, parameter_schema=:parameter_schema, 
                        icon=:icon, color=:color, is_active=:is_active, is_system=:is_system, 
                        updated_at=NOW()
                    WHERE slug=:slug
                """)
                db.execute(update_sql, w)
            else:
                print(f"Creating {w['name']}...")
                w["id"] = str(uuid.uuid4())
                insert_sql = text("""
                    INSERT INTO worker_templates 
                    (id, name, slug, description, category, default_instructions, parameter_schema, icon, color, is_active, is_system, created_at, updated_at)
                    VALUES (:id, :name, :slug, :description, :category, :default_instructions, :parameter_schema, :icon, :color, :is_active, :is_system, NOW(), NOW())
                """)
                db.execute(insert_sql, w)
        
        db.commit()
        print("Success! Worker templates seeded.")
        
    except Exception as e:
        print(f"Error seeding workers: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_new_workers()
