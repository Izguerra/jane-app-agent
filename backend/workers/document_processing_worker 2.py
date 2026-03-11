"""
Document Processing Worker

Target: Operations / Legal.
Function: OCR and Classification of documents.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

class DocumentProcessingWorker(BaseEnterpriseWorker):
    RISK_LEVEL = "medium" # May handle sensitive docs

    @classmethod
    def _execute_logic(cls, task_id: str, input_data: Dict[str, Any], service: WorkerService, db: Session) -> Dict[str, Any]:
        doc_url = input_data.get("document_url")
        if not doc_url:
            raise ValueError("Missing 'document_url'")

        service.update_task_status(task_id, current_step="Scanning Document (OCR)...", steps_total=2)
        
        # Simulate OCR extraction
        extracted_text = "Simulated content content of the document..."
        
        # Simulate Classification
        doc_type = "invoice" if "invoice" in doc_url.lower() else "contract"
        
        service.add_task_log(task_id, f"Classified document as {doc_type}")
        
        return {
            "document_type": doc_type,
            "extracted_text_snippet": extracted_text[:100],
            "page_count": 1,
            "confidence": 0.98
        }
