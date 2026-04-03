from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentPhoneNumberResponse(BaseModel):
    id: str
    phone_number: str
    friendly_name: Optional[str] = None
    country_code: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

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
    
    # Extended Wizard Fields
    avatar: Optional[str] = None
    primary_function: Optional[str] = None
    conversation_style: Optional[str] = None
    creativity_level: Optional[int] = 50
    response_length: Optional[int] = 50
    proactive_followups: Optional[bool] = True
    
    # Knowledge Base
    business_name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    services: Optional[str] = None
    hours_of_operation: Optional[str] = None
    faq: Optional[str] = None
    reference_urls: Optional[str] = None
    kb_documents_urls: Optional[List[str]] = None
    
    # Rules
    intent_rules: Optional[str] = None
    handoff_message: Optional[str] = None
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    auto_escalate: Optional[bool] = False
    
    # Widget
    deployment_channel: Optional[str] = "web_widget"
    accent_color: Optional[str] = "#3B82F6"
    widget_icon: Optional[str] = "chat"
    widget_icon_url: Optional[str] = None
    widget_position: Optional[str] = "bottom_right"
    remove_branding: Optional[bool] = False
    whitelisted_domains: Optional[str] = None
    is_active: Optional[bool] = True
    
    # Humanoid / Video Persona Settings
    anam_persona_id: Optional[str] = None
    anamPersonaId: Optional[str] = None
    tavus_replica_id: Optional[str] = None
    tavusReplicaId: Optional[str] = None
    tavus_persona_id: Optional[str] = None
    tavusPersonaId: Optional[str] = None
    avatar_provider: Optional[str] = None
    avatarProvider: Optional[str] = None
    avatar_voice_id: Optional[str] = None
    avatarVoiceId: Optional[str] = None
    use_tavus_avatar: Optional[bool] = False
    useTavusAvatar: Optional[bool] = False

    openClawInstanceId: Optional[str] = None
    open_claw_instance_id: Optional[str] = None
    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    max_depth: Optional[int] = None

    # Personal Agent Profile Fields
    owner_name: Optional[str] = None
    personal_location: Optional[str] = None
    personal_timezone: Optional[str] = None
    favorite_foods: Optional[str] = None
    favorite_restaurants: Optional[str] = None
    favorite_music: Optional[str] = None
    favorite_activities: Optional[str] = None
    other_interests: Optional[str] = None
    personal_likes: Optional[str] = None
    personal_dislikes: Optional[str] = None
    soul: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    prompt_template: Optional[str] = None
    welcome_message: Optional[str] = None
    is_orchestrator: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    phone_number_id: Optional[str] = None
    allowed_worker_types: Optional[List[str]] = None
    
    # Extended Fields
    avatar: Optional[str] = None
    primary_function: Optional[str] = None
    conversation_style: Optional[str] = None
    creativity_level: Optional[int] = None
    response_length: Optional[int] = None
    proactive_followups: Optional[bool] = None
    business_name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    services: Optional[str] = None
    hours_of_operation: Optional[str] = None
    faq: Optional[str] = None
    reference_urls: Optional[str] = None
    kb_documents_urls: Optional[List[str]] = None
    intent_rules: Optional[str] = None
    handoff_message: Optional[str] = None
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    auto_escalate: Optional[bool] = None
    deployment_channel: Optional[str] = None
    accent_color: Optional[str] = None
    widget_icon: Optional[str] = None
    widget_icon_url: Optional[str] = None
    widget_position: Optional[str] = None
    remove_branding: Optional[bool] = None
    whitelisted_domains: Optional[str] = None
    tavus_replica_id: Optional[str] = None
    tavusReplicaId: Optional[str] = None
    anam_persona_id: Optional[str] = None
    anamPersonaId: Optional[str] = None
    avatar_provider: Optional[str] = None
    avatarProvider: Optional[str] = None
    avatar_voice_id: Optional[str] = None
    avatarVoiceId: Optional[str] = None
    use_tavus_avatar: Optional[bool] = None
    useTavusAvatar: Optional[bool] = None
    openClawInstanceId: Optional[str] = None
    open_claw_instance_id: Optional[str] = None
    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    owner_name: Optional[str] = None
    personal_location: Optional[str] = None
    personal_timezone: Optional[str] = None
    favorite_foods: Optional[str] = None
    favorite_restaurants: Optional[str] = None
    favorite_music: Optional[str] = None
    favorite_activities: Optional[str] = None
    other_interests: Optional[str] = None
    personal_likes: Optional[str] = None
    personal_dislikes: Optional[str] = None
    soul: Optional[str] = None

class AgentResponse(AgentCreate):
    id: str
    workspace_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    phone_numbers: List[AgentPhoneNumberResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
