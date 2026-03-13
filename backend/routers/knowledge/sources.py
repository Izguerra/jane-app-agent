import nanoid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db
from backend.auth import get_current_user, AuthUser
from .utils import verify_workspace_access
from .models import KnowledgeBaseSource, KnowledgeBaseSourceCreate, KnowledgeBaseSourceUpdate

router = APIRouter(tags=["Knowledge Sources"])

@router.get("/{workspace_id}/knowledge-base/sources", response_model=List[KnowledgeBaseSource])
async def list_sources(workspace_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all knowledge base sources for a workspace."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    result = db.execute(text("SELECT id, workspace_id, source_type, name, config, status, last_synced_at, document_count, error_message, created_at, updated_at FROM knowledge_base_sources WHERE workspace_id = :ws_id ORDER BY created_at DESC"), {"ws_id": real_ws_id})
    return [KnowledgeBaseSource(id=r[0], workspace_id=r[1], source_type=r[2], name=r[3], config=r[4], status=r[5], last_synced_at=r[6], document_count=r[7], error_message=r[8], created_at=r[9], updated_at=r[10]) for r in result]

@router.post("/{workspace_id}/knowledge-base/sources", response_model=KnowledgeBaseSource)
async def create_source(workspace_id: str, source: KnowledgeBaseSourceCreate, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new knowledge base source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    if source.source_type not in ['website_crawler', 'file_upload', 'salesforce', 'zendesk', 'slack', 'google_drive', 'notion']:
        raise HTTPException(status_code=400, detail="Invalid source_type")
    
    source_id = nanoid.generate(size=20)
    db.execute(text("INSERT INTO knowledge_base_sources (id, workspace_id, source_type, name, config, status, document_count, created_at, updated_at) VALUES (:id, :ws_id, :st, :n, CAST(:c AS JSONB), 'pending', 0, NOW(), NOW())"), {"id": source_id, "ws_id": real_ws_id, "st": source.source_type, "n": source.name, "c": str(source.config).replace("'", '"')})
    db.commit()
    return await get_source(workspace_id, source_id, current_user, db)

@router.get("/{workspace_id}/knowledge-base/sources/{source_id}", response_model=KnowledgeBaseSource)
async def get_source(workspace_id: str, source_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific knowledge base source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    r = db.execute(text("SELECT id, workspace_id, source_type, name, config, status, last_synced_at, document_count, error_message, created_at, updated_at FROM knowledge_base_sources WHERE id = :id AND workspace_id = :ws_id"), {"id": source_id, "ws_id": real_ws_id}).fetchone()
    if not r: raise HTTPException(status_code=404, detail="Source not found")
    return KnowledgeBaseSource(id=r[0], workspace_id=r[1], source_type=r[2], name=r[3], config=r[4], status=r[5], last_synced_at=r[6], document_count=r[7], error_message=r[8], created_at=r[9], updated_at=r[10])

@router.put("/{workspace_id}/knowledge-base/sources/{source_id}", response_model=KnowledgeBaseSource)
async def update_source(workspace_id: str, source_id: str, update: KnowledgeBaseSourceUpdate, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a knowledge base source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    updates, params = [], {"id": source_id, "ws_id": real_ws_id}
    if update.name is not None: updates.append("name = :name"); params["name"] = update.name
    if update.config is not None: updates.append("config = CAST(:config AS JSONB)"); params["config"] = str(update.config).replace("'", '"')
    if update.status is not None: updates.append("status = :status"); params["status"] = update.status
    if not updates: raise HTTPException(status_code=400, detail="No fields to update")
    
    db.execute(text(f"UPDATE knowledge_base_sources SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id AND workspace_id = :ws_id"), params)
    db.commit()
    return await get_source(workspace_id, source_id, current_user, db)

@router.delete("/{workspace_id}/knowledge-base/sources/{source_id}")
async def delete_source(workspace_id: str, source_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a knowledge base source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    res = db.execute(text("DELETE FROM knowledge_base_sources WHERE id = :id AND workspace_id = :ws_id"), {"id": source_id, "ws_id": real_ws_id})
    db.commit()
    if res.rowcount == 0: raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "success"}

@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/sync")
async def sync_source(workspace_id: str, source_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Trigger manual sync for a source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    r = db.execute(text("SELECT id, source_type, config, status FROM knowledge_base_sources WHERE id = :id AND workspace_id = :ws_id"), {"id": source_id, "ws_id": real_ws_id}).fetchone()
    if not r: raise HTTPException(status_code=404, detail="Source not found")
    
    source_type, config = r[1], r[2]
    db.execute(text("UPDATE knowledge_base_sources SET status = 'syncing', updated_at = NOW() WHERE id = :id"), {"id": source_id})
    db.commit()
    
    try:
        from backend.services.source_connectors import WebsiteCrawler, FileUploadConnector
        if source_type == 'website_crawler': connector = WebsiteCrawler(source_id, real_ws_id, config)
        elif source_type == 'file_upload': connector = FileUploadConnector(source_id, real_ws_id, config)
        else: raise HTTPException(status_code=400, detail="Unsupported source type")
        
        is_valid, err = connector.validate_config()
        if not is_valid:
            db.execute(text("UPDATE knowledge_base_sources SET status = 'error', error_message = :e, updated_at = NOW() WHERE id = :id"), {"id": source_id, "e": err})
            db.commit()
            raise HTTPException(status_code=400, detail=err)
        
        res = await connector.sync()
        status = 'active' if res['documents_failed'] == 0 or res['documents_added'] > 0 else 'error'
        db.execute(text("UPDATE knowledge_base_sources SET status = :s, last_synced_at = NOW(), document_count = :d, error_message = :e, updated_at = NOW() WHERE id = :id"), {"id": source_id, "s": status, "d": res['documents_added'], "e": '; '.join(res['errors'][:3]) if res['errors'] else None})
        db.commit()
        return {"status": "success", "results": res}
    except Exception as e:
        db.execute(text("UPDATE knowledge_base_sources SET status = 'error', error_message = :e, updated_at = NOW() WHERE id = :id"), {"id": source_id, "e": str(e)})
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/pause")
async def pause_source(workspace_id: str, source_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pause syncing for a source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    db.execute(text("UPDATE knowledge_base_sources SET status = 'paused', updated_at = NOW() WHERE id = :id AND workspace_id = :ws_id"), {"id": source_id, "ws_id": real_ws_id})
    db.commit()
    return {"status": "success"}

@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/resume")
async def resume_source(workspace_id: str, source_id: str, current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Resume syncing for a source."""
    real_ws_id = verify_workspace_access(workspace_id, current_user, db)
    db.execute(text("UPDATE knowledge_base_sources SET status = 'active', updated_at = NOW() WHERE id = :id AND workspace_id = :ws_id"), {"id": source_id, "ws_id": real_ws_id})
    db.commit()
    return {"status": "success"}
