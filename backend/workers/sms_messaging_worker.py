
"""
SMS Messaging Worker (Enterprise)

Target: General Productivity / Communications
Function: Sends SMS or WhatsApp messages using the SMS Service.
Compliance: Checks permission and logs outgoing messages.
"""

import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker
from backend.services.sms_service import send_sms

logger = logging.getLogger("sms-messaging-worker")

class SMSMessagingWorker(BaseEnterpriseWorker):
    """
    Worker for sending SMS/WhatsApp messages.
    """
    RISK_LEVEL = "medium" # Outbound communication
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        recipient_number = input_data.get("recipient_number")
        message = input_data.get("message")
        force_whatsapp = input_data.get("force_whatsapp", False)
        
        if not recipient_number or not message:
            raise ValueError("Missing required parameters: recipient_number, message")
            
        # Get workspace ID from service (via task look up)
        task = service.get_task(task_id)
        if not task:
            raise ValueError("Task context lost")
            
        workspace_id = task.workspace_id
        
        service.update_task_status(task_id, status="running", current_step="Sending Message...", steps_completed=1, steps_total=2)
        service.add_task_log(task_id, f"Sending message to {recipient_number} (WhatsApp: {force_whatsapp})")
        
        
        # Execute Send
        success, result_msg = send_sms(
            to_number=recipient_number,
            message=message,
            workspace_id=workspace_id,
            force_whatsapp=force_whatsapp
        )
        
        if success:
            service.update_task_status(task_id, status="completed", current_step="Message Sent", steps_completed=2)
            service.add_task_log(task_id, f"Message sent successfully.")
            return {
                "status": "success",
                "recipient": recipient_number,
                "message": "Message sent successfully"
            }
        else:
            raise Exception(f"Failed to send message: {result_msg}")
