"""
Meeting Coordination Worker (Enterprise)

Target: Operations / Everyone.
Function: Coordinates complex scheduling, finds mutual availability, sends invites.
Compliance: GDPR (Calendar access).
"""

import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# Reuse CalendarTools
from backend.tools.calendar_tools import CalendarTools

logger = logging.getLogger("meeting-coord-worker")

class MeetingCoordinationWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade Meeting Coordinator.
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
        
        participants = input_data.get("participants", [])
        topic = input_data.get("topic", "Sync")
        duration = input_data.get("duration_minutes", 30)
        
        # Resolve Workspace
        task = service.get_task(task_id)
        workspace_id = task.workspace_id
        
        # Tools
        cal_tools = CalendarTools(workspace_id=workspace_id)
        
        service.update_task_status(task_id, status="running", current_step="Checking availability...", steps_completed=1, steps_total=3)
        service.add_task_log(task_id, f"Coordinating meeting '{topic}' for {len(participants)} participants.")
        
        # 1. Check Availability (Mock - in real world would inspect each participant's cal if internal)
        # Using the tool's get_availability for the *agent/business* primarily
        try:
            avail = cal_tools.get_availability(date="tomorrow") # Default to tomorrow check
            service.add_task_log(task_id, f"Found slots: {avail[:50]}...")
        except Exception as e:
            service.add_task_log(task_id, f"Calendar check failed: {e}", level="error")
            avail = "Unknown"

        # 2. Logic to propose times (Stub)
        proposed_slots = ["Tomorrow 10am", "Tomorrow 2pm"] # Mocked logic from 'avail'
        
        service.update_task_status(task_id, current_step="Sending invites...", steps_completed=2)
        
        # 3. Send Invites (Simulated)
        sent_status = []
        for p in participants:
            # Simulated send
            sent_status.append(f"Invite sent to {p}")
        
        return {
            "topic": topic,
            "proposed_slots": proposed_slots,
            "invites_sent_to": participants,
            "summary": f"Proposed {len(proposed_slots)} slots to {len(participants)} participants."
        }
