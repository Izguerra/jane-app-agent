from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    agent_id: Optional[str] = None
    agent_config: Optional[dict] = None
    session_id: Optional[str] = None # Allow client to specify/reset session

class ChatResponse(BaseModel):
    response: str

class DocumentRequest(BaseModel):
    doc_id: str
    text: str
