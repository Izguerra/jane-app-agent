from typing import Dict, Any
from sqlalchemy.orm import Session

# Handle both import contexts (uvicorn vs direct execution)
try:
    from backend.database import SessionLocal
    from backend.models_db import AgentSettings, Clinic
except ModuleNotFoundError:
    from database import SessionLocal
    from models_db import AgentSettings, Clinic

# TODO: In a real multi-tenant app, this ID comes from the authenticated user's session
DEFAULT_CLINIC_ID = 1

DEFAULT_SETTINGS = {
    "voice_id": "alloy",
    "language": "en",
    "prompt_template": (
        "You are Jane, a helpful AI assistant for a healthcare practice. "
        "You can help with scheduling, answering questions about the clinic, and general inquiries. "
        "Keep your responses concise and conversational.\n\n"
        "IMPORTANT: When users ask about business information (hours, location, services, policies, etc.), "
        "you MUST use the get_business_info() tool to retrieve accurate information. "
        "For specific questions about policies or FAQs, use the search_knowledge_base() tool. "
        "Always provide information from these tools rather than making assumptions."
    ),
    "is_active": True
}

def get_settings(clinic_id: int = DEFAULT_CLINIC_ID) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        settings = db.query(AgentSettings).filter(AgentSettings.clinic_id == clinic_id).first()
        
        if not settings:
            # Check if clinic exists, if not create dummy clinic for demo
            clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
            if not clinic:
                # Create default clinic for demo purposes if it doesn't exist
                clinic = Clinic(id=clinic_id, team_id=1, name="Demo Clinic")
                db.add(clinic)
                db.commit()

            # Create default settings
            settings = AgentSettings(
                clinic_id=clinic_id,
                voice_id=DEFAULT_SETTINGS["voice_id"],
                language=DEFAULT_SETTINGS["language"],
                prompt_template=DEFAULT_SETTINGS["prompt_template"],
                is_active=DEFAULT_SETTINGS["is_active"]
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
        return {
            "voice_id": settings.voice_id,
            "language": settings.language,
            "prompt_template": settings.prompt_template,
            "is_active": settings.is_active
        }
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return DEFAULT_SETTINGS
    finally:
        db.close()

def save_settings(new_settings: Dict[str, Any], clinic_id: int = DEFAULT_CLINIC_ID):
    db = SessionLocal()
    try:
        settings = db.query(AgentSettings).filter(AgentSettings.clinic_id == clinic_id).first()
        
        if not settings:
            # Should exist due to get_settings, but handle just in case
            settings = AgentSettings(clinic_id=clinic_id)
            db.add(settings)
        
        if "voice_id" in new_settings:
            settings.voice_id = new_settings["voice_id"]
        if "language" in new_settings:
            settings.language = new_settings["language"]
        if "prompt_template" in new_settings:
            settings.prompt_template = new_settings["prompt_template"]
        if "is_active" in new_settings:
            settings.is_active = new_settings["is_active"]
            
        db.commit()
    except Exception as e:
        print(f"Error saving settings: {e}")
        db.rollback()
        raise e
    finally:
        db.close()
