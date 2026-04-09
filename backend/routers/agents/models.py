from pydantic import BaseModel, ConfigDict, Field, AliasChoices
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
    is_orchestrator: Optional[bool] = False
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
    
    # Humanoid / Video Persona Settings (Consolidated with Aliases)
    anam_persona_id: Optional[str] = Field(None, validation_alias=AliasChoices("anam_persona_id", "anamPersonaId"))
    tavus_replica_id: Optional[str] = Field(None, validation_alias=AliasChoices("tavus_replica_id", "tavusReplicaId"))
    avatar_provider: Optional[str] = Field(None, validation_alias=AliasChoices("avatar_provider", "avatarProvider"))
    avatar_voice_id: Optional[str] = Field(None, validation_alias=AliasChoices("avatar_voice_id", "avatarVoiceId"))
    use_tavus_avatar: Optional[bool] = Field(False, validation_alias=AliasChoices("use_tavus_avatar", "useTavusAvatar"))
    open_claw_instance_id: Optional[str] = Field(None, validation_alias=AliasChoices("open_claw_instance_id", "openClawInstanceId"))

    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    max_depth: Optional[int] = None

    # Personal Agent Profile Fields
    owner_name: Optional[str] = Field(None, validation_alias=AliasChoices("owner_name", "ownerName"))
    personal_location: Optional[str] = Field(None, validation_alias=AliasChoices("personal_location", "personalLocation"))
    personal_timezone: Optional[str] = Field(None, validation_alias=AliasChoices("personal_timezone", "personalTimezone"))
    favorite_foods: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_foods", "favoriteFoods"))
    favorite_restaurants: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_restaurants", "favoriteRestaurants"))
    favorite_music: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_music", "favoriteMusic"))
    favorite_activities: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_activities", "favoriteActivities"))
    other_interests: Optional[str] = Field(None, validation_alias=AliasChoices("other_interests", "otherInterests"))
    personal_likes: Optional[str] = Field(None, validation_alias=AliasChoices("personal_likes", "personalLikes"))
    personal_dislikes: Optional[str] = Field(None, validation_alias=AliasChoices("personal_dislikes", "personalDislikes"))
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
    
    # Consolidated Avatar Fields with Aliases
    tavus_replica_id: Optional[str] = Field(None, validation_alias=AliasChoices("tavus_replica_id", "tavusReplicaId"))
    anam_persona_id: Optional[str] = Field(None, validation_alias=AliasChoices("anam_persona_id", "anamPersonaId"))
    avatar_provider: Optional[str] = Field(None, validation_alias=AliasChoices("avatar_provider", "avatarProvider"))
    avatar_voice_id: Optional[str] = Field(None, validation_alias=AliasChoices("avatar_voice_id", "avatarVoiceId"))
    use_tavus_avatar: Optional[bool] = Field(None, validation_alias=AliasChoices("use_tavus_avatar", "useTavusAvatar"))
    open_claw_instance_id: Optional[str] = Field(None, validation_alias=AliasChoices("open_claw_instance_id", "openClawInstanceId"))
    
    agent_type: Optional[str] = None
    personal_preferences: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    owner_name: Optional[str] = Field(None, validation_alias=AliasChoices("owner_name", "ownerName"))
    personal_location: Optional[str] = Field(None, validation_alias=AliasChoices("personal_location", "personalLocation"))
    personal_timezone: Optional[str] = Field(None, validation_alias=AliasChoices("personal_timezone", "personalTimezone"))
    favorite_foods: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_foods", "favoriteFoods"))
    favorite_restaurants: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_restaurants", "favoriteRestaurants"))
    favorite_music: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_music", "favoriteMusic"))
    favorite_activities: Optional[str] = Field(None, validation_alias=AliasChoices("favorite_activities", "favoriteActivities"))
    other_interests: Optional[str] = Field(None, validation_alias=AliasChoices("other_interests", "otherInterests"))
    personal_likes: Optional[str] = Field(None, validation_alias=AliasChoices("personal_likes", "personalLikes"))
    personal_dislikes: Optional[str] = Field(None, validation_alias=AliasChoices("personal_dislikes", "personalDislikes"))
    soul: Optional[str] = None

class AgentResponse(AgentCreate):
    id: str
    workspace_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    phone_numbers: List[AgentPhoneNumberResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
