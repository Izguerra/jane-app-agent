"""
Worker Executor

Background task executor that polls for pending worker tasks and runs them
autonomously using AI agents.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models_db import WorkerTask
from backend.services.worker_service import WorkerService
from backend.prompts.worker_prompts import get_worker_prompt, WORKER_REWARD_MODEL


logger = logging.getLogger("worker-executor")


class WorkerExecutor:
    """
    Background executor that picks up pending tasks and runs them autonomously.
    
    Usage:
        executor = WorkerExecutor()
        executor.start()  # Start background polling
        # ... app runs ...
        executor.stop()   # Graceful shutdown
    """
    
    def __init__(
        self,
        poll_interval: int = 1,
        max_concurrent_tasks: int = 3
    ):
        self.poll_interval = poll_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._active_tasks: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        
        # Worker type to handler mapping
        self._handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register built-in worker handlers."""
        from backend.workers.job_search_worker import JobSearchWorker
        from backend.workers.lead_research_worker import LeadResearchWorker
        from backend.workers.content_writer_worker import ContentWriterWorker
        
        self._handlers["job-search"] = JobSearchWorker.execute
        self._handlers["lead-research"] = LeadResearchWorker.execute
        self._handlers["content-writer"] = ContentWriterWorker.execute
        
        # Enterprise Workers (Batch A)
        from backend.workers.sales_outreach_worker import SalesOutreachWorker
        from backend.workers.faq_resolution_worker import FAQResolutionWorker
        from backend.workers.meeting_coordination_worker import MeetingCoordinationWorker
        self._handlers["sales-outreach"] = SalesOutreachWorker.run
        self._handlers["faq-resolution"] = FAQResolutionWorker.run
        self._handlers["meeting-coordination"] = MeetingCoordinationWorker.run

        # Enterprise Workers (Batch B)
        from backend.workers.order_status_worker import OrderStatusWorker
        from backend.workers.hr_onboarding_worker import HROnboardingWorker
        from backend.workers.payment_billing_worker import PaymentBillingWorker
        from backend.workers.it_support_worker import ITSupportWorker
        self._handlers["order-status"] = OrderStatusWorker.run
        self._handlers["hr-onboarding"] = HROnboardingWorker.run
        self._handlers["payment-billing"] = PaymentBillingWorker.run
        self._handlers["it-support"] = ITSupportWorker.run

        # Enterprise Workers (Batch C)
        from backend.workers.intelligent_routing_worker import IntelligentRoutingWorker
        from backend.workers.data_entry_worker import DataEntryWorker
        from backend.workers.document_processing_worker import DocumentProcessingWorker
        from backend.workers.content_moderation_worker import ContentModerationWorker
        from backend.workers.sentiment_escalation_worker import SentimentEscalationWorker
        from backend.workers.translation_worker import TranslationWorker
        from backend.workers.compliance_worker import ComplianceWorker

        self._handlers["intelligent-routing"] = IntelligentRoutingWorker.run
        self._handlers["data-entry"] = DataEntryWorker.run
        self._handlers["document-processing"] = DocumentProcessingWorker.run
        self._handlers["content-moderation"] = ContentModerationWorker.run
        self._handlers["sentiment-escalation"] = SentimentEscalationWorker.run
        self._handlers["translation-localization"] = TranslationWorker.run
        self._handlers["compliance-risk"] = ComplianceWorker.run
        
        from backend.workers.email_worker import EmailWorker
        self._handlers["email-worker"] = EmailWorker.execute
        
        from backend.workers.sms_messaging_worker import SMSMessagingWorker
        self._handlers["sms-messaging"] = SMSMessagingWorker.run

        # External API Workers
        from backend.workers.weather_worker import WeatherWorker
        self._handlers["weather-worker"] = WeatherWorker.run
        
        from backend.workers.flight_tracker_worker import FlightTrackerWorker
        self._handlers["flight-tracker"] = FlightTrackerWorker.run

        from backend.workers.map_worker import MapWorker
        self._handlers["map-worker"] = MapWorker.run

        from backend.workers.openclaw_worker import OpenClawWorker
        self._handlers["openclaw"] = OpenClawWorker.run
    
    def register_handler(self, worker_type: str, handler: Callable):
        """Register a custom worker handler."""
        self._handlers[worker_type] = handler
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    def start(self):
        """Start the background polling loop."""
        if self._running:
            logger.warning("WorkerExecutor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"WorkerExecutor started (polling every {self.poll_interval}s)")
    
    def stop(self):
        """Stop the executor gracefully."""
        logger.info("WorkerExecutor stopping...")
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        logger.info("WorkerExecutor stopped")
    
    # =========================================================================
    # Polling Loop
    # =========================================================================
    
    def _poll_loop(self):
        """Main polling loop that checks for pending tasks."""
        while self._running:
            try:
                self._check_for_tasks()
            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
            
            time.sleep(self.poll_interval)
    
    def _check_for_tasks(self):
        """Check for pending tasks and claim one if capacity allows."""
        with self._lock:
            active_count = len(self._active_tasks)
        
        if active_count >= self.max_concurrent_tasks:
            return  # At capacity
        
        db = SessionLocal()
        try:
            # Find and claim a pending task
            # EXCLUDE openclaw tasks - they are handled by the container workers themselves
            task = db.query(WorkerTask).filter(
                WorkerTask.status == "pending",
                WorkerTask.worker_type != "openclaw"
            ).order_by(WorkerTask.created_at.asc()).first()
            
            if not task:
                return  # No pending tasks
            
            # Claim the task
            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()
            
            task_id = task.id
            worker_type = task.worker_type
            
            logger.info(f"Claimed task {task_id} ({worker_type})")
            
            # Start processing in a new thread
            thread = threading.Thread(
                target=self._process_task,
                args=(task_id,),
                daemon=True
            )
            
            with self._lock:
                self._active_tasks[task_id] = thread
            
            thread.start()
            
        finally:
            db.close()
    
    # =========================================================================
    # Task Processing
    # =========================================================================
    
    def _process_task(self, task_id: str):
        """Process a single task."""
        db = SessionLocal()
        service = WorkerService(db)
        
        try:
            task = service.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            worker_type = task.worker_type
            input_data = task.input_data or {}
            
            logger.info(f"Processing task {task_id} ({worker_type})")
            
            # Update initial step
            service.update_task_status(
                task_id,
                status="running",
                current_step="Initializing worker...",
                steps_completed=0,
                steps_total=5  # Default estimate
            )
            
            # Get handler for this worker type
            handler = self._handlers.get(worker_type)
            if not handler:
                raise ValueError(f"No handler for worker type: {worker_type}")
            
            # Execute the worker
            result = handler(
                task_id=task_id,
                input_data=input_data,
                service=service,
                db=db
            )
            
            # Mark complete
            service.update_task_status(
                task_id,
                status="completed",
                current_step="Done"
            )
            
            # Save output
            task = service.get_task(task_id)
            task.output_data = result
            task.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            
            try:
                service.update_task_status(
                    task_id,
                    status="failed",
                    error_message=str(e)
                )
            except Exception as update_error:
                logger.error(f"Failed to update task status: {update_error}")
        
        finally:
            db.close()
            
            # Remove from active tasks
            with self._lock:
                self._active_tasks.pop(task_id, None)
    
    # =========================================================================
    # Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        with self._lock:
            active_task_ids = list(self._active_tasks.keys())
        
        return {
            "running": self._running,
            "poll_interval": self.poll_interval,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": len(active_task_ids),
            "active_task_ids": active_task_ids
        }


# Global executor instance
_executor: Optional[WorkerExecutor] = None


def get_executor() -> WorkerExecutor:
    """Get or create the global executor instance."""
    global _executor
    if _executor is None:
        _executor = WorkerExecutor()
    return _executor


def start_executor():
    """Start the global executor."""
    executor = get_executor()
    executor.start()
    return executor


def stop_executor():
    """Stop the global executor."""
    global _executor
    if _executor:
        _executor.stop()
        _executor = None
