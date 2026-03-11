"""
FAQ Resolution Worker (Enterprise)

Target: Customer Support.
Function: Answers customer questions using Knowledge Base (Confluence/Docs).
Compliance: Public data only (Low Risk).
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# We can reuse the KnowledgeBaseService
from backend.knowledge_base import KnowledgeBaseService

logger = logging.getLogger("faq-resolution-worker")

class FAQResolutionWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade FAQ Support Agent.
    """
    RISK_LEVEL = "low"
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        question = input_data.get("question")
        customer_id = input_data.get("customer_id")
        
        if not question:
            raise ValueError("Missing 'question' parameter")
            
        kb = KnowledgeBaseService()
        
        service.update_task_status(task_id, status="running", current_step="Searching Knowledge Base...", steps_completed=1, steps_total=2)
        
        # 1. Search KB
        # Assuming we can get workspace_id from the task context
        # But for this worker, we need to pass it or look it up.
        # WorkerService doesn't pass the task object directly to execute, only ID.
        # So we fetch task.
        task = service.get_task(task_id)
        if not task:
            raise Exception("Task context lost")
            
        docs = kb.search(question, workspace_id=task.workspace_id)
        
        found_answers = []
        if docs:
            service.add_task_log(task_id, f"Found {len(docs)} relevant articles.")
            found_answers = [d.get("text", "")[:300] + "..." for d in docs]
        else:
            service.add_task_log(task_id, "No direct KB matches found.", level="warning")

        # 2. Synthesize Answer (Mock generation for now, real app would call LLM)
        service.update_task_status(task_id, current_step="Drafting Response...", steps_completed=2)
        
        if found_answers:
            draft_answer = f"Based on our internal docs:\n\n" + "\n\n".join(found_answers)
            confidence = "high"
        else:
            draft_answer = "I could not find a specific article about this. Validating with human support..."
            confidence = "low"

        return {
            "question": question,
            "sources_found": len(docs),
            "draft_answer": draft_answer,
            "confidence": confidence,
            "summary": f"Process complete. Confidence: {confidence}"
        }
