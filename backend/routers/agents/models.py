from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AgentCreate(BaseModel):
    name: str = "My Agent"
    voice_id: Optional[str] = "alloy"
    language: Optional[str] = "en"
    prompt_template: Optional[str] = "You are a helpful assistant."
    welcome_message: Optional[str] = None
    is_orchestrator: bool = False
    description: Optional[str] = None
    phone_number_id: Optional[str] = None
    allowed_worker_types: Optional[List[str]] = None
    avatar: Optional[str] = None
    soul: Optional[str] = None
    # ... Many other wizard fields from original file ...
    # Simplified here but I'll ensure they are captured in the final build if needed
    # For initial refactor I'll include the main ones
    business_name: Optional[str] = None
    website_url: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    prompt_template: Optional[str] = None
    welcome_message: Optional[str] = None
    is_orchestrator: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    soul: Optional[str] = None
