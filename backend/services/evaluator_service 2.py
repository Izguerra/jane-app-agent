from sqlalchemy.orm import Session
from backend.models_db import WorkerTask, WorkerTemplate, Appointment, Customer, Communication
from backend.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class EvaluatorService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_task(self, task_id: str) -> bool:
        """
        Evaluate if a task was successful based on its outcome definition.
        Returns True if successful, False otherwise.
        Updates task.outcome_status and task.outcome_score.
        """
        task = self.db.query(WorkerTask).filter(WorkerTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found for evaluation")
            return False

        if task.status != "completed":
            logger.warning(f"Task {task.id} is not completed, skipping evaluation")
            return False

        worker_type = task.worker_type
        outcome_config = {}
        
        # Fetch template for specific logic if needed
        template = self.db.query(WorkerTemplate).filter(WorkerTemplate.slug == worker_type).first()
        if template and template.evaluation_logic:
            outcome_config = template.evaluation_logic

        # Default to neutral if no specific logic
        outcome_status = "neutral"
        outcome_score = 0.5
        
        try:
            # --- EVALUATION LOGIC ROUTER ---
            
            if worker_type == "appointment-setter":
                # Check for appointment creation
                outcome_status, outcome_score = self._verify_appointment(task)
                
            elif worker_type in ["lead-qualifier", "lead-researcher"]:
                # Check for CRM update or enrichment
                outcome_status, outcome_score = self._verify_lead_qualification(task)
                
            elif worker_type == "support-agent":
                # Check outcome based on sentiment or ticket closure
                outcome_status, outcome_score = self._verify_support_resolution(task)
                
            elif worker_type == "content-writer":
                # Content generation is usually success if output exists
                if task.output_data and "content" in task.output_data:
                    outcome_status = "success"
                    outcome_score = 1.0
                else:
                    outcome_status = "failure"
                    outcome_score = 0.0
            
            else:
                # Default behavior: If task completed without error, assume success
                # But mark as 'neutral' outcome for billing purposes unless configured otherwise
                if task.error_message:
                    outcome_status = "failure"
                    outcome_score = 0.0
                else:
                    outcome_status = "success" # Or 'neutral' if we don't want to bill? 
                    # For now, let's assume 'success' for generic tasks means they did the job.
                    outcome_score = 1.0

            # Update Task
            task.outcome_status = outcome_status
            task.outcome_score = outcome_score
            
            # If success, calculate billing
            if outcome_status == "success":
                # Get price from template
                price = template.outcome_price if template else 0
                if price > 0:
                    task.outcome_fee_cents = price
                    task.billing_amount = price # Legacy compat or redundancy
            
            self.db.commit()
            
            return outcome_status == "success"

        except Exception as e:
            logger.error(f"Error evaluating task {task.id}: {e}")
            task.outcome_status = "error"
            self.db.commit()
            return False

    def _verify_appointment(self, task: WorkerTask) -> tuple[str, float]:
        """Verify appointment was actually booked."""
        # Method 1: Check output data for appointment_id
        if task.output_data and task.output_data.get("appointment_id"):
            appt_id = task.output_data.get("appointment_id")
            appt = self.db.query(Appointment).filter(Appointment.id == appt_id).first()
            if appt:
                return "success", 1.0
        
        # Method 2: Check for any appointment created for this customer in the last hour
        # This is a fallback if the worker forgot to return the ID
        if task.customer_id:
             # Logic to find recent appointment could go here
             pass

        return "failure", 0.0

    def _verify_lead_qualification(self, task: WorkerTask) -> tuple[str, float]:
        """Verify lead was qualified."""
        if task.customer_id:
            customer = self.db.query(Customer).filter(Customer.id == task.customer_id).first()
            if customer:
                # If stage moved to MQL/SQL or similar
                if customer.lifecycle_stage in ["MQL", "SQL", "Opportunity"]:
                     return "success", 1.0
                # Or if specific fields were enriched (checking logic needed)
        
        # Fallback: check if output data indicates success
        if task.output_data.get("qualified") is True:
            return "success", 1.0
            
        return "neutral", 0.5

    def _verify_support_resolution(self, task: WorkerTask) -> tuple[str, float]:
        """Verify support ticket resolution."""
        # Simple check: Did it complete successfully?
        # Ideally check if a ticket was marked 'solved'
        return "success", 1.0
