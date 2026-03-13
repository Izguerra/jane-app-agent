import json
import nanoid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from .utils import verify_workspace_access

router = APIRouter(tags=["Knowledge - File Uploads"])

@router.post("/{workspace_id}/knowledge-base/upload")
async def upload_file(workspace_id: str, file: UploadFile = File(...), current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upload a file and immediately index it."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    try:
        from backend.services.storage_service import get_storage_service
        storage = get_storage_service()
        
        safe_filename = f"{nanoid.generate(size=10)}_{file.filename.replace(' ', '_')}"
        await file.seek(0)
        s3_key = storage.upload_file(file.file, safe_filename, file.content_type)
        if not s3_key: raise HTTPException(status_code=500, detail="Upload failed")
            
        source_id, config = nanoid.generate(size=20), {"file_path": s3_key, "storage_type": "s3", "original_filename": file.filename, "content_type": file.content_type}
        db.execute(text("INSERT INTO knowledge_base_sources (id, workspace_id, source_type, name, config, status, document_count, created_at, updated_at) VALUES (:id, :ws_id, 'file_upload', :name, CAST(:config AS JSONB), 'syncing', 0, NOW(), NOW())"), {"id": source_id, "ws_id": real_ws_id, "name": file.filename, "config": json.dumps(config)})
        db.commit()
    
        from backend.services.source_connectors import FileUploadConnector
        res = await FileUploadConnector(source_id, real_ws_id, config).sync()
        status = 'active' if res['documents_failed'] == 0 else 'error'
        db.execute(text("UPDATE knowledge_base_sources SET status = :s, last_synced_at = NOW(), document_count = :d, error_message = :e, updated_at = NOW() WHERE id = :id"), {"id": source_id, "s": status, "d": res['documents_added'], "e": '; '.join(res['errors']) if res['errors'] else None})
        db.commit()
        
        return {"url": f"/api/uploads/{safe_filename}", "source_id": source_id, "filename": file.filename, "sync_result": res}
    except Exception as e:
        if 'source_id' in locals():
            db.execute(text("UPDATE knowledge_base_sources SET status = 'error', error_message = :e, updated_at = NOW() WHERE id = :id"), {"id": source_id, "e": str(e)})
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))
