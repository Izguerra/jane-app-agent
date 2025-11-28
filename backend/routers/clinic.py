from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models_db import Clinic, KnowledgeDocument
import json

router = APIRouter(prefix="/clinics", tags=["clinics"])

class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    business_hours: Optional[str] = None  # JSON string
    services: Optional[str] = None
    faq: Optional[str] = None  # JSON string
    reference_urls: Optional[str] = None  # JSON string

@router.get("/me")
async def get_my_clinic(db: Session = Depends(get_db)):
    # TODO: Get clinic_id from authenticated user's team
    clinic_id = 1
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        # Create default clinic if it doesn't exist
        clinic = Clinic(
            id=clinic_id,
            team_id=1,
            name="My Business",
            address="",
            phone="",
            website="",
            description="",
            business_hours="{}",
            services="",
            faq="[]",
            reference_urls="[]"
        )
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
    
    return {
        "id": clinic.id,
        "name": clinic.name,
        "address": clinic.address or "",
        "phone": clinic.phone or "",
        "website": clinic.website or "",
        "description": clinic.description or "",
        "business_hours": clinic.business_hours or "{}",
        "services": clinic.services or "",
        "faq": clinic.faq or "[]",
        "reference_urls": clinic.reference_urls or "[]"
    }

@router.put("/me")
async def update_my_clinic(clinic_update: ClinicUpdate, db: Session = Depends(get_db)):
    clinic_id = 1
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # Update fields
    if clinic_update.name is not None:
        clinic.name = clinic_update.name
    if clinic_update.address is not None:
        clinic.address = clinic_update.address
    if clinic_update.phone is not None:
        clinic.phone = clinic_update.phone
    if clinic_update.website is not None:
        clinic.website = clinic_update.website
    if clinic_update.description is not None:
        clinic.description = clinic_update.description
    if clinic_update.business_hours is not None:
        clinic.business_hours = clinic_update.business_hours
    if clinic_update.services is not None:
        clinic.services = clinic_update.services
    if clinic_update.faq is not None:
        clinic.faq = clinic_update.faq
    if clinic_update.reference_urls is not None:
        clinic.reference_urls = clinic_update.reference_urls
    
    db.commit()
    db.refresh(clinic)
    
    return {"status": "success", "data": clinic_update}

@router.get("/context")
async def get_business_context(db: Session = Depends(get_db)):
    """Get business context for agent knowledge retrieval"""
    clinic_id = 1
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        return {}
    
    # Parse JSON fields
    business_hours = json.loads(clinic.business_hours) if clinic.business_hours else {}
    faq = json.loads(clinic.faq) if clinic.faq else []
    reference_urls = json.loads(clinic.reference_urls) if clinic.reference_urls else []
    
    # Get knowledge documents
    documents = db.query(KnowledgeDocument).filter(KnowledgeDocument.clinic_id == clinic_id).all()
    
    return {
        "name": clinic.name,
        "address": clinic.address,
        "phone": clinic.phone,
        "website": clinic.website,
        "description": clinic.description,
        "business_hours": business_hours,
        "services": clinic.services,
        "faq": faq,
        "reference_urls": reference_urls,
        "documents": [{"filename": doc.filename, "content": doc.content} for doc in documents]
    }

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a knowledge document"""
    clinic_id = 1
    
    # Read file content
    content = await file.read()
    text_content = content.decode('utf-8') if file.content_type == 'text/plain' else ""
    
    # TODO: For PDFs, use a library like PyPDF2 to extract text
    # For now, just store text files
    
    doc = KnowledgeDocument(
        clinic_id=clinic_id,
        filename=file.filename,
        content=text_content,
        file_type=file.content_type,
        file_path=f"/uploads/{file.filename}"  # TODO: Implement actual file storage
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {"status": "success", "document_id": doc.id, "filename": doc.filename}

@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all knowledge documents"""
    clinic_id = 1
    documents = db.query(KnowledgeDocument).filter(KnowledgeDocument.clinic_id == clinic_id).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]

@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge document"""
    clinic_id = 1
    
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.clinic_id == clinic_id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    
    return {"status": "success"}
