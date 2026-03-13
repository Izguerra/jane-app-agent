from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GeneralSettings(BaseModel):
    company_name: str
    support_email: str
    default_language: str
    timezone: str

class SecurityOverview(BaseModel):
    two_factor_enabled: bool
    password_last_changed: Optional[datetime]
    active_sessions_count: int

class APIKey(BaseModel):
    id: str
    name: str
    key_prefix: str
    last_used_at: Optional[datetime]
    created_at: datetime

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    key_prefix: str

class ActiveSession(BaseModel):
    id: str
    device_name: str
    location: str
    ip_address: str
    last_active_at: datetime
    created_at: datetime

class PlatformIntegration(BaseModel):
    id: str
    provider: str
    display_name: str
    description: Optional[str]
    is_enabled: bool
    customer_count: int = 0
    health_status: str = "unknown"
    last_checked: Optional[datetime] = None

class IntegrationToggle(BaseModel):
    is_enabled: bool

class HealthCheckResponse(BaseModel):
    provider: str
    status: str
    message: str
    checked_at: datetime
