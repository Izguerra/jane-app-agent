from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import nanoid

from backend.database import get_db
from backend.auth import get_current_user

router = APIRouter(prefix="/workspaces", tags=["knowledge-base"])

# Pydantic Models
class KnowledgeBaseSourceConfig(BaseModel):
    url: Optional[str] = None
    file_path: Optional[str] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    # Add more config fields as needed

class KnowledgeBaseSourceCreate(BaseModel):
    source_type: str  # 'website_crawler', 'file_upload', 'salesforce', etc.
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

    class Config:
        from_attributes = True


# Helper function to verify workspace access
def verify_workspace_access(workspace_id: str, current_user: dict, db: Session) -> str:
    """Verify user has access to workspace and resolve Team ID to Workspace ID if needed"""
    
    real_workspace_id = workspace_id
    
    # Check if an Organization ID (org_) or Team ID (tm_) was passed instead of Workspace ID
    if workspace_id.startswith(("org_", "tm_")):
        # Resolve to the workspace for this team/org
        row = db.execute(text("SELECT id, team_id FROM workspaces WHERE team_id = :team_id"), {"team_id": workspace_id}).fetchone()
        if not row:
             # Auto-create workspace if missing (lazy init)
             from backend.database import generate_workspace_id
             ws_id = generate_workspace_id()
             db.execute(text("INSERT INTO workspaces (id, team_id, name, created_at, updated_at) VALUES (:id, :team_id, :name, NOW(), NOW())"), {
                 "id": ws_id,
                 "team_id": workspace_id,
                 "name": f"Workspace for {workspace_id}"
             })
             db.commit()
             real_workspace_id = ws_id
             print(f"DEBUG: Auto-created workspace {ws_id} for {workspace_id}")
        else:
             real_workspace_id = row[0]
             print(f"DEBUG: Resolved {workspace_id} to workspace {real_workspace_id}")
        
    # Verify Access logic (simpler version matching agents.py)
    # 1. Get Workspace Details
    workspace = db.execute(text("SELECT id, team_id FROM workspaces WHERE id = :id"), {"id": real_workspace_id}).fetchone()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # 2. Check Permissions
    # If admin/owner, pass.
    # If user's team_id matches workspace's team_id, pass.
    if current_user.role in ['supaagent_admin', 'owner']:
        return real_workspace_id
        
    if current_user.team_id == workspace[1]:
        return real_workspace_id
        
    raise HTTPException(status_code=403, detail="Access denied to this workspace")


@router.get("/{workspace_id}/knowledge-base/sources", response_model=List[KnowledgeBaseSource])
async def list_sources(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all knowledge base sources for a workspace"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    result = db.execute(text("""
        SELECT id, workspace_id, source_type, name, config, status, 
               last_synced_at, document_count, error_message, created_at, updated_at
        FROM knowledge_base_sources
        WHERE workspace_id = :workspace_id
        ORDER BY created_at DESC
    """), {"workspace_id": real_workspace_id})
    
    sources = []
    for row in result:
        sources.append(KnowledgeBaseSource(
            id=row[0],
            workspace_id=row[1],
            source_type=row[2],
            name=row[3],
            config=row[4],
            status=row[5],
            last_synced_at=row[6],
            document_count=row[7],
            error_message=row[8],
            created_at=row[9],
            updated_at=row[10]
        ))
    
    return sources


@router.post("/{workspace_id}/knowledge-base/sources", response_model=KnowledgeBaseSource)
async def create_source(
    workspace_id: str,
    source: KnowledgeBaseSourceCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new knowledge base source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    # Validate source_type
    valid_types = ['website_crawler', 'file_upload', 'salesforce', 'zendesk', 'slack', 'google_drive', 'notion']
    if source.source_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid source_type. Must be one of: {', '.join(valid_types)}")
    
    # Generate ID
    source_id = nanoid.generate(size=20)
    
    # Insert source
    db.execute(text("""
        INSERT INTO knowledge_base_sources 
        (id, workspace_id, source_type, name, config, status, document_count, created_at, updated_at)
        VALUES (:id, :workspace_id, :source_type, :name, CAST(:config AS JSONB), 'pending', 0, NOW(), NOW())
    """), {
        "id": source_id,
        "workspace_id": real_workspace_id,
        "source_type": source.source_type,
        "name": source.name,
        "config": str(source.config).replace("'", '"')  # Convert to JSON string
    })
    db.commit()
    
    # Fetch and return created source
    result = db.execute(text("""
        SELECT id, workspace_id, source_type, name, config, status, 
               last_synced_at, document_count, error_message, created_at, updated_at
        FROM knowledge_base_sources
        WHERE id = :id
    """), {"id": source_id}).fetchone()
    
    return KnowledgeBaseSource(
        id=result[0],
        workspace_id=result[1],
        source_type=result[2],
        name=result[3],
        config=result[4],
        status=result[5],
        last_synced_at=result[6],
        document_count=result[7],
        error_message=result[8],
        created_at=result[9],
        updated_at=result[10]
    )


@router.get("/{workspace_id}/knowledge-base/sources/{source_id}", response_model=KnowledgeBaseSource)
async def get_source(
    workspace_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    result = db.execute(text("""
        SELECT id, workspace_id, source_type, name, config, status, 
               last_synced_at, document_count, error_message, created_at, updated_at
        FROM knowledge_base_sources
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return KnowledgeBaseSource(
        id=result[0],
        workspace_id=result[1],
        source_type=result[2],
        name=result[3],
        config=result[4],
        status=result[5],
        last_synced_at=result[6],
        document_count=result[7],
        error_message=result[8],
        created_at=result[9],
        updated_at=result[10]
    )


@router.put("/{workspace_id}/knowledge-base/sources/{source_id}", response_model=KnowledgeBaseSource)
async def update_source(
    workspace_id: str,
    source_id: str,
    update: KnowledgeBaseSourceUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a knowledge base source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    # Build update query dynamically
    updates = []
    params = {"id": source_id, "workspace_id": real_workspace_id}
    
    if update.name is not None:
        updates.append("name = :name")
        params["name"] = update.name
    
    if update.config is not None:
        updates.append("config = CAST(:config AS JSONB)")
        params["config"] = str(update.config).replace("'", '"')
    
    if update.status is not None:
        updates.append("status = :status")
        params["status"] = update.status
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    
    db.execute(text(f"""
        UPDATE knowledge_base_sources
        SET {', '.join(updates)}
        WHERE id = :id AND workspace_id = :workspace_id
    """), params)
    db.commit()
    
    # Fetch and return updated source
    # Note: reusing get_source logic locally or calling helper if abstracted
    # Here we just re-query
    result = db.execute(text("""
        SELECT id, workspace_id, source_type, name, config, status, 
               last_synced_at, document_count, error_message, created_at, updated_at
        FROM knowledge_base_sources
        WHERE id = :id AND workspace_id = :workspace_id
    """), params).fetchone()
    
    return KnowledgeBaseSource(
        id=result[0],
        workspace_id=result[1],
        source_type=result[2],
        name=result[3],
        config=result[4],
        status=result[5],
        last_synced_at=result[6],
        document_count=result[7],
        error_message=result[8],
        created_at=result[9],
        updated_at=result[10]
    )


@router.delete("/{workspace_id}/knowledge-base/sources/{source_id}")
async def delete_source(
    workspace_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge base source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    # Delete source (documents will have source_id set to NULL due to ON DELETE SET NULL)
    result = db.execute(text("""
        DELETE FROM knowledge_base_sources
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {"status": "success", "message": "Source deleted"}


@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/sync")
async def sync_source(
    workspace_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger manual sync for a source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    # Get source details
    result = db.execute(text("""
        SELECT id, source_type, config, status
        FROM knowledge_base_sources
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Source not found")
    
    source_type = result[1]
    config = result[2]
    
    # Update status to syncing
    db.execute(text("""
        UPDATE knowledge_base_sources
        SET status = 'syncing', updated_at = NOW()
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id})
    db.commit()
    
    try:
        # Import and instantiate appropriate connector
        from backend.services.source_connectors import WebsiteCrawler, FileUploadConnector
        
        if source_type == 'website_crawler':
            connector = WebsiteCrawler(source_id, real_workspace_id, config)
        elif source_type == 'file_upload':
            connector = FileUploadConnector(source_id, real_workspace_id, config)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")
        
        # Validate config
        is_valid, error_msg = connector.validate_config()
        if not is_valid:
            db.execute(text("""
                UPDATE knowledge_base_sources
                SET status = 'error', error_message = :error, updated_at = NOW()
                WHERE id = :id
            """), {"id": source_id, "error": error_msg})
            db.commit()
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Run sync
        sync_result = await connector.sync()
        
        # Update source with results
        if sync_result['documents_failed'] > 0 and sync_result['documents_added'] == 0:
            status = 'error'
            error_message = '; '.join(sync_result['errors'][:3])  # First 3 errors
        else:
            status = 'active'
            error_message = None
        
        db.execute(text("""
            UPDATE knowledge_base_sources
            SET status = :status, 
                last_synced_at = NOW(),
                document_count = :doc_count,
                error_message = :error,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": source_id,
            "status": status,
            "doc_count": sync_result['documents_added'],
            "error": error_message
        })
        db.commit()
        
        return {
            "status": "success",
            "message": "Sync completed",
            "results": sync_result
        }
    
    except Exception as e:
        # Update status to error
        db.execute(text("""
            UPDATE knowledge_base_sources
            SET status = 'error', error_message = :error, updated_at = NOW()
            WHERE id = :id
        """), {"id": source_id, "error": str(e)})
        db.commit()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/pause")
async def pause_source(
    workspace_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause syncing for a source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    db.execute(text("""
        UPDATE knowledge_base_sources
        SET status = 'paused', updated_at = NOW()
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id})
    db.commit()
    
    return {"status": "success", "message": "Source paused"}


@router.post("/{workspace_id}/knowledge-base/sources/{source_id}/resume")
async def resume_source(
    workspace_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume syncing for a source"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    db.execute(text("""
        UPDATE knowledge_base_sources
        SET status = 'active', updated_at = NOW()
        WHERE id = :id AND workspace_id = :workspace_id
    """), {"id": source_id, "workspace_id": real_workspace_id})
    db.commit()
    
    return {"status": "success", "message": "Source resumed"}


@router.post("/{workspace_id}/knowledge-base/upload")
async def upload_file(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to Storage and immediately index it into the Knowledge Base"""
    real_workspace_id = verify_workspace_access(workspace_id, current_user, db)
    
    try:
        import json
        from backend.services.storage_service import get_storage_service
        storage = get_storage_service()
        
        # 1. Upload to S3/Spaces
        safe_filename = f"{nanoid.generate(size=10)}_{file.filename.replace(' ', '_')}"
        
        # Important: Reset file pointer to beginning before upload
        await file.seek(0)
        
        s3_key = storage.upload_file(file.file, safe_filename, file.content_type)
        
        if not s3_key:
             raise HTTPException(status_code=500, detail="Failed to upload file to storage")
            
        # 2. Create Knowledge Base Source
        source_id = nanoid.generate(size=20)
        config = {
            "file_path": s3_key,
            "storage_type": "s3",
            "original_filename": file.filename,
            "content_type": file.content_type
        }
        
        db.execute(text("""
            INSERT INTO knowledge_base_sources 
            (id, workspace_id, source_type, name, config, status, document_count, created_at, updated_at)
            VALUES (:id, :workspace_id, 'file_upload', :name, CAST(:config AS JSONB), 'syncing', 0, NOW(), NOW())
        """), {
            "id": source_id,
            "workspace_id": real_workspace_id,
            "name": file.filename,
            "config": json.dumps(config)
        })
        db.commit()
    
        # 3. Trigger Sync (Extraction & Vectorization)
        # Note: We pass the full config which now contains storage info
        from backend.services.source_connectors import FileUploadConnector
        connector = FileUploadConnector(source_id, real_workspace_id, config)
        sync_result = await connector.sync()
        
        # Update source status
        status = 'active' if sync_result['documents_failed'] == 0 else 'error'
        error_msg = '; '.join(sync_result['errors']) if sync_result['errors'] else None
        
        db.execute(text("""
            UPDATE knowledge_base_sources
            SET status = :status, 
            last_synced_at = NOW(),
            document_count = :doc_count,
            error_message = :error,
            updated_at = NOW()
            WHERE id = :id
        """), {
            "id": source_id,
            "status": status,
            "doc_count": sync_result['documents_added'],
            "error": error_msg
        })
        db.commit()
        
        return {
            "url": f"/api/uploads/{safe_filename}", 
            "source_id": source_id,
            "filename": file.filename,
            "sync_result": sync_result
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Indexing Error Traceback: {error_trace}")
        
        # Write to file for debugging
        try:
            with open("backend/error.log", "w") as f:
                f.write(error_trace)
        except:
            pass
            
        # Update status to error (if source_id exists)
        if 'source_id' in locals():
            try:
                 db.execute(text("""
                    UPDATE knowledge_base_sources
                    SET status = 'error', error_message = :error, updated_at = NOW()
                    WHERE id = :id
                """), {"id": source_id, "error": str(e)})
                 db.commit()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
