"""
IT Support Worker (Enterprise)

Target: Internal IT.
Function: Troubleshooting and Password Resets.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# Reuse KnowledgeBase for troubleshooting guides
from backend.knowledge_base import KnowledgeBaseService

logger = logging.getLogger("it-support-worker")

class ITSupportWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade IT Agent.
    """
    RISK_LEVEL = "medium"
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        issue_type = input_data.get("issue_type") # password_reset, software, hardware
        employee_id = input_data.get("employee_id")
        details = input_data.get("details", "")
        
        if not issue_type:
            raise ValueError("Missing 'issue_type'")
            
        task = service.get_task(task_id)
        kb = KnowledgeBaseService()
        
        service.update_task_status(task_id, status="running", current_step="Analyzing Issue...", steps_completed=1)
        
        # 1. Search IT Docs
        query = f"IT procedure for {issue_type} {details}"
        docs = kb.search(query, workspace_id=task.workspace_id)
        
        # 2. Execute Action
        resolution_steps = []
        if docs:
            resolution_steps = [d.get("text", "")[:200] for d in docs]
            service.add_task_log(task_id, f"Found {len(docs)} IT protocols.")
            
        action_taken = "ticket_created"
        
        if issue_type == "password_reset":
            # Real impl would call Okta/ActiveDirectory
            service.add_task_log(task_id, "Password reset requested. Sending magic link to employee email (Simulated).")
            action_taken = "reset_link_sent"
            
        return {
            "issue": issue_type,
            "employee": employee_id,
            "action_taken": action_taken,
            "relevant_protocols": resolution_steps
        }
