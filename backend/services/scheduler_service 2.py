
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import re
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.models_db import WorkerSchedule
from backend.services.worker_service import WorkerService

logger = logging.getLogger("scheduler-service")

class SchedulerService:
    def __init__(self, db: Session):
        self.db = db
        self.worker_service = WorkerService(db)

    def create_schedule(
        self,
        workspace_id: str,
        worker_type: str,
        schedule_expression: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> WorkerSchedule:
        """
        Create a new schedule.
        schedule_expression examples: "daily at 9:00", "every monday at 10:00", "hourly"
        """
        import uuid
        
        # Calculate initial next_run_at
        next_run = self._calculate_next_run(schedule_expression)
        
        schedule = WorkerSchedule(
            id=f"sch_{str(uuid.uuid4())}",
            workspace_id=workspace_id,
            worker_type=worker_type,
            schedule_expression=schedule_expression,
            input_data=input_data,
            next_run_at=next_run,
            created_by_user_id=user_id,
            is_active=True
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def process_due_schedules(self):
        """
        Poll and execute due schedules.
        Should be called periodically (e.g. every minute).
        """
        # Use server-side time for comparison to avoid timezone mismatch
        from sqlalchemy.sql import func
        
        # Log server time
        server_time = self.db.execute(func.now()).scalar()
        logger.info(f"Checking schedules due before server time: {server_time}")

        due_schedules = self.db.query(WorkerSchedule).filter(
            WorkerSchedule.is_active == True,
            WorkerSchedule.next_run_at <= func.now()
        ).all()
        
        logger.info(f"Found {len(due_schedules)} due schedules.")
        
        for schedule in due_schedules:
            try:
                self._execute_schedule(schedule)
            except Exception as e:
                logger.error(f"Failed to execute schedule {schedule.id}: {e}")

    def _execute_schedule(self, schedule: WorkerSchedule):
        """Execute the schedule and update next run time."""
        logger.info(f"Executing schedule {schedule.id} ({schedule.worker_type})")
        
        # 1. Create the worker task
        task = self.worker_service.create_task(
            workspace_id=schedule.workspace_id,
            worker_type=schedule.worker_type,
            input_data=schedule.input_data
        )
        
        # 2. Update schedule state
        schedule.last_run_at = datetime.now(timezone.utc)
        
        # 3. Calculate next run
        # If calculation fails (e.g. "once"), deactivate
        next_run = self._calculate_next_run(schedule.schedule_expression, schedule.last_run_at)
        
        if next_run:
            schedule.next_run_at = next_run
            logger.info(f"Next run for {schedule.id} set to {next_run}")
        else:
            schedule.is_active = False # Deactivate if no next run (meaning it was one-off or valid period ended? currently assuming recurring)
            schedule.next_run_at = None
            logger.info(f"Schedule {schedule.id} completed (no future run valid). Deactivating.")
            
        self.db.commit()

    def _calculate_next_run(self, expression: str, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next run time based on expression.
        from_time defaults to now.
        
        Supported formats:
        - "daily at HH:MM"
        - "every day at HH:MM"
        - "hourly"
        - "every X hours"
        """
        if from_time is None:
            from_time = datetime.now(timezone.utc)
            
        exp = expression.lower().strip()
        
        # Hourly
        if exp == "hourly":
            return from_time + timedelta(hours=1)
            
        # Daily at specific time
        # regex for "daily at 14:30" or "every day at 9am"
        # Simplify: assume 24h format for now or basic am/pm parsing
        
        time_match = re.search(r'(?:daily|every day) at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', exp)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period:
                if period == 'pm' and hour < 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            
            # Construct target time for today
            target = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If target is in past, move to tomorrow
            if target <= from_time:
                target += timedelta(days=1)
                
            return target

        # Default fallback: Schedule for 24 hours from now if "daily" detected but no time
        if "daily" in exp or "every day" in exp:
             return from_time + timedelta(days=1)
             
        # Fallback to None (invalid)
        logger.warning(f"Could not parse schedule expression: {expression}")
        return None


async def run_scheduler():
    """Background task to run the scheduler loop."""
    import asyncio
    from backend.database import SessionLocal
    
    logger.info("Scheduler started.")
    while True:
        try:
            db = SessionLocal()
            try:
                service = SchedulerService(db)
                service.process_due_schedules()
                
                # --- GLOBAL SESSION CLEANUP ---
                # Check for workspaces with ongoing sessions and run cleanup
                from backend.models_db import Communication
                from backend.services.crm_service import CRMService
                
                # distinct query to find relevant workspaces only
                active_workspace_ids = db.query(Communication.workspace_id).filter(
                    Communication.status == "ongoing"
                ).distinct().all()
                
                if active_workspace_ids:
                    crm = CRMService(db)
                    for (ws_id,) in active_workspace_ids:
                        crm.cleanup_stale_sessions(ws_id)
                # -----------------------------
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            
        await asyncio.sleep(60) # Poll every 60 seconds

