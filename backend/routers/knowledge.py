from fastapi import APIRouter, HTTPException, Depends
from backend.models import DocumentRequest
from backend.services import get_kb_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/upload")
async def upload_document(request: DocumentRequest, kb_service=Depends(get_kb_service)):
    try:
        kb_service.upsert_document(request.doc_id, request.text)
        return {"status": "success", "doc_id": request.doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
