from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import time
import threading

# Handle both import contexts (uvicorn vs direct execution)
try:
    from backend.database import SessionLocal, generate_settings_id
    from backend.models_db import Agent, Workspace, Team
except ModuleNotFoundError:
    from database import SessionLocal, generate_settings_id
    from models_db import Agent, Workspace, Team

DEFAULT_SETTINGS = {
    "voice_id": "alloy",
    "language": "en",
    "prompt_template": (
        "You are SupaAgent, a helpful AI assistant for a healthcare practice. "
        "You can help with scheduling, answering questions about the clinic, and general inquiries. "
        "Keep your responses concise and conversational."
    ),
    "welcome_message": "Hi there! I'm SupaAgent, your AI assistant. How can I help you today?",
    "is_active": True,
    "allowed_worker_types": ["weather-worker", "flight-tracker", "map-worker", "web-search", "advanced-browsing"]
}

# TTL-based settings cache: prevents stale settings in long-running voice/avatar workers
# while still reducing DB load for rapid successive HTTP requests.
_settings_cache: Dict[str, tuple] = {}  # {workspace_id: (timestamp, settings_dict)}
_settings_cache_lock = threading.Lock()
_SETTINGS_TTL = 60  # seconds

def get_settings(workspace_id: str = None) -> Dict[str, Any]:
    if workspace_id is None:
        # Fallback for development/demo if absolutely necessary
        workspace_id = "ws_default"
    
    # TTL cache check — return cached result if fresh enough
    with _settings_cache_lock:
        if workspace_id in _settings_cache:
            cached_time, cached_result = _settings_cache[workspace_id]
            if time.time() - cached_time < _SETTINGS_TTL:
                return cached_result.copy()  # Return a copy to avoid mutation
        
    db = SessionLocal()
    
    # Resolve Team ID to Workspace ID if needed
    if workspace_id and isinstance(workspace_id, str) and workspace_id.startswith(("tm_", "org_")):
        # Try to find workspace by team_id
        ws = db.query(Workspace).filter(Workspace.team_id == workspace_id).first()
        if ws:
            print(f"DEBUG: Resolved Team ID {workspace_id} to Workspace ID {ws.id}")
            workspace_id = ws.id
        else:
             print(f"DEBUG: Could not resolve Team ID {workspace_id} to a workspace")

    try:
        print(f"DEBUG: get_settings called for workspace_id={workspace_id}")
        
        # Try to find an orchestrator agent first, or just any agent
        settings = db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.is_orchestrator == True
        ).first()
        
        if settings:
             print(f"DEBUG: Found orchestrator agent: {settings.id}")
        
        if not settings:
            # Fallback to any agent
            settings = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
            if settings:
                 print(f"DEBUG: Found fallback agent: {settings.id}")
        
        if not settings:
            # Check if workspace exists
            workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                # Find a valid team
                team = db.query(Team).first()
                if not team:
                    # Should unlikely happen if seeded, but create one just in case
                    team = Team(id="team_default", name="Default Team")
                    db.add(team)
                    db.commit()
                
                workspace = Workspace(id=workspace_id, team_id=team.id, name="Demo Workspace")
                db.add(workspace)
                db.commit()

            # Create default agent
            gen_id = generate_settings_id().replace("st", "ag")
            print(f"DEBUG: Generating Agent ID: {gen_id}")
            settings = Agent(
                id=gen_id,
                workspace_id=workspace_id,
                name="Default Agent",
                voice_id=DEFAULT_SETTINGS["voice_id"],
                language=DEFAULT_SETTINGS["language"],
                prompt_template=DEFAULT_SETTINGS["prompt_template"],
                welcome_message=DEFAULT_SETTINGS["welcome_message"],
                is_active=DEFAULT_SETTINGS["is_active"],
                allowed_worker_types=DEFAULT_SETTINGS["allowed_worker_types"],
                is_orchestrator=True # Default to orchestrator if it's the first one
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
        # Parse settings JSON
        extended_settings = settings.settings or {}
        
        result = {
            "agent_id": settings.id,
            "name": settings.name,
            "voice_id": settings.voice_id,
            "language": settings.language,
            "prompt_template": settings.prompt_template,
            "welcome_message": settings.welcome_message,
            "is_active": settings.is_active,
            "workspace_id": settings.workspace_id,
            "is_orchestrator": settings.is_orchestrator,
            
            # Extended Settings
            "business_name": extended_settings.get("business_name"),
            "website_url": extended_settings.get("website_url"),
            "email": extended_settings.get("email"),
            "phone": extended_settings.get("phone"),
            "address": extended_settings.get("address"),
            "services": extended_settings.get("services"),
            "hours_of_operation": extended_settings.get("hours_of_operation"),
            "faq": extended_settings.get("faq"),
            "reference_urls": extended_settings.get("reference_urls"),
            "kb_documents_urls": extended_settings.get("kb_documents_urls"),
            
            "creativity_level": extended_settings.get("creativity_level", 50),
            "response_length": extended_settings.get("response_length", 50),
            "proactive_followups": extended_settings.get("proactive_followups", True),
            "intent_rules": extended_settings.get("intent_rules"),
            "handoff_message": extended_settings.get("handoff_message"),
            "auto_escalate": extended_settings.get("auto_escalate", False),
            
            "avatar": extended_settings.get("avatar"),
            "primary_function": extended_settings.get("primary_function"),
            "conversation_style": extended_settings.get("conversation_style"),
            
            # Application Settings
            "allowed_worker_types": settings.allowed_worker_types or [],
            "soul": settings.soul
        }
        
        # Store in TTL cache
        with _settings_cache_lock:
            _settings_cache[workspace_id] = (time.time(), result)
        
        return result
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return DEFAULT_SETTINGS
    finally:
        db.close()

def invalidate_settings_cache(workspace_id: str = None):
    """Invalidate the TTL cache for a workspace, or all workspaces."""
    with _settings_cache_lock:
        if workspace_id:
            _settings_cache.pop(workspace_id, None)
        else:
            _settings_cache.clear()

def save_settings(new_settings: Dict[str, Any], workspace_id: int = None):
    if workspace_id is None:
        workspace_id = 1

    db = SessionLocal()
    try:
        # Update orchestrator or first found agent
        settings = db.query(Agent).filter(
            Agent.workspace_id == workspace_id,
            Agent.is_orchestrator == True
        ).first()
        
        if not settings:
            settings = db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
            
        if not settings:
            # Create new if doesn't exist
            settings = Agent(id=generate_settings_id().replace("st", "ag"), workspace_id=workspace_id, is_orchestrator=True)
            db.add(settings)
        
        if "voice_id" in new_settings:
            settings.voice_id = new_settings["voice_id"]
        if "language" in new_settings:
            settings.language = new_settings["language"]
        if "prompt_template" in new_settings:
            settings.prompt_template = new_settings["prompt_template"]
        if "welcome_message" in new_settings:
            settings.welcome_message = new_settings["welcome_message"]
        if "is_active" in new_settings:
            settings.is_active = new_settings["is_active"]
        if "soul" in new_settings:
            settings.soul = new_settings["soul"]
            
        db.commit()
        # Invalidate settings cache so voice/avatar workers pick up changes immediately
        invalidate_settings_cache(workspace_id)
    except Exception as e:
        print(f"Error saving settings: {e}")
        db.rollback()
        raise e
    finally:
        db.close()
