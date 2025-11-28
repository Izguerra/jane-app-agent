from fastapi import APIRouter, HTTPException, Depends
from backend.models import ChatRequest, ChatResponse
from backend.services import get_agent_manager

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, agent_manager=Depends(get_agent_manager)):
    try:
        response = agent_manager.chat(request.message)
        return ChatResponse(response=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
