"""
Order Status Worker (Enterprise)

Target: Customer Support / E-commerce.
Function: Retrieves real-time order tracking from Shopify/Integrations.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

# Reuse ShopifyTools
from backend.tools.shopify_tools import ShopifyTools

logger = logging.getLogger("order-status-worker")

class OrderStatusWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade Order Status Agent.
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
        
        order_number = input_data.get("order_number")
        customer_email = input_data.get("customer_email")
        
        if not order_number:
            raise ValueError("Missing 'order_number'")
        
        # Get Workspace ID from task
        task = service.get_task(task_id)
        if not task:
            raise Exception("Task context missing")

        # Initialize Shopify Tools
        tools = ShopifyTools(workspace_id=task.workspace_id)
        
        service.update_task_status(task_id, status="running", current_step="Connecting to Store...", steps_completed=1, steps_total=2)
        
        # Check Status
        try:
            # We pass a placeholder name since the tool requires it but doesn't strictly validate it against DB yet
            result_text = tools.check_order_status(
                order_number=order_number, 
                verify_name="Authorized Agent", 
                verify_email=customer_email or "agent@internal"
            )
            
            # Simple parsing of the text result for structured output
            # In a real impl, we'd refactor ShopifyTools to return dicts, but for now we parse text
            status = "unknown"
            if "fulfillment: fulfilled" in result_text.lower():
                status = "shipped"
            elif "fulfillment: unfulfilled" in result_text.lower():
                status = "processing"
            elif "not found" in result_text.lower():
                status = "not_found"
            
            service.add_task_log(task_id, f"Shopify Result: {result_text}")
            
            return {
                "order_number": order_number,
                "status_text": result_text,
                "normalized_status": status,
                "provider": "shopify"
            }
            
        except Exception as e:
            service.add_task_log(task_id, f"Shopify lookup failed: {e}", level="error")
            raise e
