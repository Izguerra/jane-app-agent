"""
Reminder Scheduler Service

Schedules and triggers appointment reminders.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models_db import Appointment, AppointmentReminder, Customer
from backend.services.outbound_calling_service import outbound_calling_service
from backend.services.outbound_data_service import outbound_data_service
from backend.database import generate_comm_id
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ReminderSchedulerService:
    @staticmethod
    def schedule_reminder(
        appointment_id: str,
        reminder_time: datetime,
        db: Session
    ) -> AppointmentReminder:
        """Schedule a reminder for an appointment"""
        reminder = AppointmentReminder(
            id=generate_comm_id(),
            appointment_id=appointment_id,
            reminder_time=reminder_time,
            status="pending"
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder
    
    @staticmethod
    def get_pending_reminders(db: Session) -> List[AppointmentReminder]:
        """Get all pending reminders that are due"""
        now = datetime.utcnow()
        reminders = db.query(AppointmentReminder).filter(
            AppointmentReminder.status == "pending",
            AppointmentReminder.reminder_time <= now
        ).all()
        return reminders
    
    @staticmethod
    def process_reminder(reminder: AppointmentReminder, db: Session):
        """Process a single reminder by initiating an outbound call"""
        try:
            # Get appointment
            appointment = db.query(Appointment).filter(
                Appointment.id == reminder.appointment_id
            ).first()
            
            if not appointment:
                logger.error(f"Appointment {reminder.appointment_id} not found for reminder {reminder.id}")
                reminder.status = "failed"
                db.commit()
                return
            
            # Get customer
            customer = db.query(Customer).filter(
                Customer.id == appointment.customer_id
            ).first()
            
            if not customer or not customer.phone:
                logger.error(f"Customer {appointment.customer_id} not found or has no phone for reminder {reminder.id}")
                reminder.status = "failed"
                db.commit()
                return
            
            # Build call context
            call_context = outbound_data_service.build_call_context(
                call_intent="appointment_reminder",
                workspace_id=appointment.workspace_id,
                db=db,
                appointment_id=appointment.id,
                customer_id=customer.id
            )
            
            # Initiate call
            result = outbound_calling_service.initiate_call(
                workspace_id=appointment.workspace_id,
                to_phone=customer.phone,
                call_intent="appointment_reminder",
                call_context=call_context,
                customer_id=customer.id,
                db=db
            )
            
            # Update reminder with communication ID
            reminder.communication_id = result["communication_id"]
            reminder.status = "sent"
            db.commit()
            
            logger.info(f"Reminder {reminder.id} processed successfully, call initiated: {result['communication_id']}")
        
        except Exception as e:
            logger.error(f"Failed to process reminder {reminder.id}: {str(e)}")
            reminder.status = "failed"
            db.commit()
    
    @staticmethod
    def process_pending_reminders(db: Session):
        """Process all pending reminders"""
        reminders = ReminderSchedulerService.get_pending_reminders(db)
        logger.info(f"Processing {len(reminders)} pending reminders")
        
        for reminder in reminders:
            ReminderSchedulerService.process_reminder(reminder, db)
    
    @staticmethod
    def create_default_reminders_for_appointment(
        appointment: Appointment,
        db: Session
    ):
        """Create default reminders for an appointment (24h and 1h before)"""
        appointment_time = appointment.appointment_date
        
        # 24 hour reminder
        reminder_24h = appointment_time - timedelta(hours=24)
        if reminder_24h > datetime.utcnow():
            ReminderSchedulerService.schedule_reminder(
                appointment_id=appointment.id,
                reminder_time=reminder_24h,
                db=db
            )
        
        # 1 hour reminder
        reminder_1h = appointment_time - timedelta(hours=1)
        if reminder_1h > datetime.utcnow():
            ReminderSchedulerService.schedule_reminder(
                appointment_id=appointment.id,
                reminder_time=reminder_1h,
                db=db
            )


# Singleton instance
reminder_scheduler_service = ReminderSchedulerService()
