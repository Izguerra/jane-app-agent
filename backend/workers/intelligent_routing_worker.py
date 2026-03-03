"""
Intelligent Routing Worker

Target: Operations / Support.
Function: Analyzes incoming ticket/call intent and routes to the correct department.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

class IntelligentRoutingWorker(BaseEnterpriseWorker):
    RISK_LEVEL = "low"

    @classmethod
    def _execute_logic(cls, task_id: str, input_data: Dict[str, Any], service: WorkerService, db: Session) -> Dict[str, Any]:
        text = input_data.get("text", "")
        if not text:
            raise ValueError("Input 'text' is required for routing.")

        # Simulate Intent Analysis (In prod, use LLM/Classifier)
        intent = "general_inquiry"
        department = "support"
        confidence = 0.85

        text_lower = text.lower()
        if "refund" in text_lower or "bill" in text_lower:
            intent = "billing_issue"
            department = "finance"
            confidence = 0.95
        elif "bug" in text_lower or "error" in text_lower:
            intent = "technical_issue"
            department = "engineering"
            confidence = 0.90
        elif "price" in text_lower or "demo" in text_lower:
            intent = "sales_inquiry"
            department = "sales"
        
        service.add_task_log(task_id, f"Routed '{text[:50]}...' to {department} (Intent: {intent})")

        return {
            "intent": intent,
            "department": department,
            "confidence": confidence,
            "routing_action": f"forward_to_{department}"
        }
