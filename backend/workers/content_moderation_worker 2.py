"""
Content Moderation Worker

Target: Trust & Safety.
Function: Flags toxic or policy-violating content.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

class ContentModerationWorker(BaseEnterpriseWorker):
    RISK_LEVEL = "high" 

    @classmethod
    def _execute_logic(cls, task_id: str, input_data: Dict[str, Any], service: WorkerService, db: Session) -> Dict[str, Any]:
        content = input_data.get("content", "")
        
        # Mock Moderation Logic
        flagged = False
        categories = []
        
        bad_words = ["spam", "fraud", "attack"]
        for w in bad_words:
            if w in content.lower():
                flagged = True
                categories.append(w)
        
        return {
            "flagged": flagged,
            "categories": categories,
            "safety_score": 0.1 if flagged else 0.95
        }
