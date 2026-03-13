from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class WorkerTemplateResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    parameter_schema: Dict[str, Any]
    required_tools: List[str]
    required_integrations: List[str]
    icon: str
    color: str
    is_active: bool
    
    class Config:
        from_attributes = True

class CreateTaskRequest(BaseModel):
    worker_type: str
    input_data: Dict[str, Any]
    customer_id: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    worker_type: str
    worker_name: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    steps_completed: int
    steps_total: Optional[int] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class TaskStatsResponse(BaseModel):
    status_counts: Dict[str, int]
    total_tasks: int
    total_tokens_used: int

class CreateInstanceRequest(BaseModel):
    worker_type: str = "openclaw"
    tier: str = "standard"
    name: Optional[str] = None
    llm_model: str = "claude-3-5-sonnet"
    llm_api_key: Optional[str] = None

class InstanceResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    worker_type: str
    tier: str
    files_disk_size_gb: int
    status: str
    container_id: Optional[str] = None
    ip_address: Optional[str] = None
    is_external: bool = False
    connection_url: Optional[str] = None
    monthly_cost_cents: int
    created_at: str

    class Config:
        from_attributes = True

class RateTaskRequest(BaseModel):
    rating: int
    feedback: Optional[str] = None

class CompleteTaskRequest(BaseModel):
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    status: str = "completed"
    tokens_used: int = 0
