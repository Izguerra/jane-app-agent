from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class KnowledgeBaseSourceConfig(BaseModel):
    url: Optional[str] = None
    file_path: Optional[str] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None

class KnowledgeBaseSourceCreate(BaseModel):
    source_type: str
    name: str
    config: dict

class KnowledgeBaseSourceUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None

class KnowledgeBaseSource(BaseModel):
    id: str
    workspace_id: str
    source_type: str
    name: str
    config: dict
    status: str
    last_synced_at: Optional[datetime]
    document_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
