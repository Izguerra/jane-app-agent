from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class DocumentRequest(BaseModel):
    doc_id: str
    text: str
