"""
Payment & Billing Worker (Enterprise)

Target: Finance.
Function: Invoice status and payment checks. Uses Stripe if available.
"""

import logging
import os
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService
from backend.workers.base_enterprise_worker import BaseEnterpriseWorker

logger = logging.getLogger("payment-billing-worker")

class PaymentBillingWorker(BaseEnterpriseWorker):
    """
    Enterprise-grade Payment Agent.
    """
    RISK_LEVEL = "high" # Financial data
    
    @classmethod
    def _execute_logic(
        cls, 
        task_id: str, 
        input_data: Dict[str, Any], 
        service: WorkerService, 
        db: Session
    ) -> Dict[str, Any]:
        
        action = input_data.get("action") # check_status, refund, invoice
        transaction_id = input_data.get("transaction_id")
        email = input_data.get("email")
        
        if not action:
            raise ValueError("Missing 'action'")
            
        task = service.get_task(task_id)
        
        service.update_task_status(task_id, status="running", current_step="Connecting to Gateway...", steps_completed=1)
        
        # Try to use real Stripe from Integration (Priority 1)
        stripe_key = None
        try:
            from backend.models_db import Integration
            import json
            integration = db.query(Integration).filter(
                Integration.workspace_id == task.workspace_id,
                Integration.provider == "stripe",
                Integration.is_active == True
            ).first()
            
            if integration and integration.credentials:
                creds = json.loads(integration.credentials)
                stripe_key = creds.get("api_key") or creds.get("secret_key")
        except Exception:
            pass
            
        # Fallback to Env Var (Priority 2)
        if not stripe_key:
            stripe_key = os.getenv("STRIPE_SECRET_KEY")

        if stripe_key:
            import stripe
            stripe.api_key = stripe_key
            
            try:
                result_data = {}
                
                if action == "check_status":
                    # Search by transaction ID or email
                    if transaction_id:
                        pi = stripe.PaymentIntent.retrieve(transaction_id)
                        result_data = {"status": pi.status, "amount": pi.amount, "currency": pi.currency}
                    elif email:
                        customers = stripe.Customer.list(email=email, limit=1)
                        if customers.data:
                            cust = customers.data[0]
                            result_data = {"customer_id": cust.id, "balance": cust.balance}
                        else:
                            result_data = {"error": "Customer not found in Stripe"}
                    else:
                        raise ValueError("Transaction ID or Email required for Stripe check")
                        
                elif action == "invoice":
                    # Create basic invoice (Stub availability)
                     result_data = {"status": "Invoice generation requires full line-item details. (Not implemented in this worker version)"}

                return {
                    "action": action,
                    "provider": "stripe",
                    "result": result_data
                }
                
            except Exception as e:
                service.add_task_log(task_id, f"Stripe operation failed: {e}", level="error")
                return {"error": str(e), "provider": "stripe"}
        
        else:
             return {
                 "status": "skipped",
                 "reason": "STRIPE_SECRET_KEY not configured. Cannot perform real payment operations."
             }
