from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import json
import io
from pypdf import PdfReader

from backend.database import get_db, generate_workspace_id
from backend.models_db import Workspace, Document as DocumentModel
from backend.auth import get_current_user, AuthUser
from backend.services import get_kb_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    services: Optional[str] = None
    business_hours: Optional[str] = None
    faq: Optional[str] = None
    reference_urls: Optional[str] = None

class Document(BaseModel):
    id: int
    filename: str
    uploaded_at: str

@router.get("/me")
async def get_my_workspace(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Get workspace for authenticated user's team
    team_id = current_user.team_id
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    
    if not workspace:
        # Create default workspace for new team
        workspace = Workspace(
            id=generate_workspace_id(),
            team_id=team_id,
            name="Variation Tattoo Studio",
            address="123 Ink St, Art City",
            phone="555-0123",
            website="https://variationtattoo.com",
            description="Custom tattoo studio offering various styles.",
            services="Custom Tattoos\nCover-ups\nPiercings",
            business_hours=json.dumps({"monday": {"open": "10:00", "close": "20:00"}}),
            faq=json.dumps([{"question": "Do you take walk-ins?", "answer": "Yes, subject to availability."}]),
            reference_urls=json.dumps(["https://variationtattoo.com/aftercare"])
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    
    return {
        "id": workspace.id,
        "name": workspace.name,
        "address": workspace.address,
        "phone": workspace.phone,
        "website": workspace.website,
        "description": workspace.description,
        "services": workspace.services,
        "business_hours": workspace.business_hours,
        "faq": workspace.faq,
        "reference_urls": workspace.reference_urls
    }

@router.put("/me")
async def update_my_workspace(
    workspace_update: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Get workspace for authenticated user's team
    team_id = current_user.team_id
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Update only the fields that were provided
    update_data = workspace_update.model_dump(exclude_unset=True)
    print(f"DEBUG: Updating workspace {workspace.id} with data: {update_data}")
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    db.commit()
    db.refresh(workspace)
    
    return {
        "status": "success",
        "data": {
            "id": workspace.id,
            "name": workspace.name,
            "address": workspace.address,
            "phone": workspace.phone,
            "website": workspace.website,
            "description": workspace.description,
            "services": workspace.services,
            "business_hours": workspace.business_hours,
            "faq": workspace.faq,
            "reference_urls": workspace.reference_urls
        }
    }

@router.get("/documents")
async def get_documents(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    team_id = current_user.team_id
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    if not workspace:
        return []
        
    documents = db.query(DocumentModel).filter(DocumentModel.workspace_id == workspace.id).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
        }
        for doc in documents
    ]

@router.post("/documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
    kb_service = Depends(get_kb_service)
):
    print(f"DEBUG: upload_documents called. User: {current_user.email if current_user else 'None'}")
    print(f"DEBUG: Files received: {len(files)}")
    for f in files:
        print(f"DEBUG: File: {f.filename}, Content-Type: {f.content_type}")

    team_id = current_user.team_id
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    if not workspace:
        print("DEBUG: Workspace not found")
        raise HTTPException(status_code=404, detail="Workspace not found")

    uploaded_docs = []
    errors = []

    for file in files:
        try:
            # Read file content
            content = await file.read()
            text_content = ""
            
            if file.filename.lower().endswith(".pdf"):
                try:
                    pdf = PdfReader(io.BytesIO(content))
                    for page in pdf.pages:
                        text_content += page.extract_text() + "\n"
                except Exception as e:
                    print(f"Error extracting PDF text from {file.filename}: {e}")
                    errors.append(f"Failed to read PDF {file.filename}")
                    continue
            else:
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"Failed to decode text file {file.filename}")
                    continue
                
            if not text_content.strip():
                errors.append(f"File {file.filename} is empty")
                continue

            # Add to Knowledge Base (Pinecone)
            # We use filename as doc_id for now, or generate a unique one
            doc_id = f"{workspace.id}_{file.filename}"
            kb_service.upsert_document(doc_id, text_content)
            
            # Save to DB
            # Check if exists first to update?
            existing_doc = db.query(DocumentModel).filter(
                DocumentModel.workspace_id == workspace.id, 
                DocumentModel.filename == file.filename
            ).first()
            
            if existing_doc:
                # Update existing? Or duplicate?
                # For now, update timestamp implicitly (or do nothing)
                db_doc = existing_doc
            else:
                db_doc = DocumentModel(
                    workspace_id=workspace.id,
                    filename=file.filename,
                    file_type=file.filename.split('.')[-1] if '.' in file.filename else 'txt'
                )
                db.add(db_doc)
            
            db.commit()
            db.refresh(db_doc)
            
            uploaded_docs.append({"id": db_doc.id, "filename": db_doc.filename})
            
        except Exception as e:
            print(f"Upload error for {file.filename}: {e}")
            errors.append(f"Error uploading {file.filename}: {str(e)}")

    if not uploaded_docs and errors:
        raise HTTPException(status_code=500, detail=f"Upload failed: {', '.join(errors)}")

    return {"status": "success", "uploaded": uploaded_docs, "errors": errors}

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
    kb_service = Depends(get_kb_service)
):
    team_id = current_user.team_id
    workspace = db.query(Workspace).filter(Workspace.team_id == team_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id, DocumentModel.workspace_id == workspace.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove from Pinecone
    pinecone_doc_id = f"{workspace.id}_{doc.filename}"
    kb_service.delete_document(pinecone_doc_id)
    
    db.delete(doc)
    db.commit()
    
    return {"status": "success", "deleted": doc_id}

@router.get("/context")
async def get_clinic_context(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Returns a consolidated text blob of the clinic's information
    for the AI agent to use as context.
    """
    workspace_data = await get_my_workspace(db, current_user)
    
    context = f"""
    Business Name: {workspace_data['name']}
    Address: {workspace_data['address']}
    Phone: {workspace_data['phone']}
    Website: {workspace_data['website']}
    Description: {workspace_data['description']}
    Services: {workspace_data['services']}
    
    FAQ:
    {workspace_data['faq']}
    
    Business Hours:
    {workspace_data['business_hours']}
    """
    return {"context": context}
