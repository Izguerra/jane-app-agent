import logging
import calendar
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models_db import Customer, Communication, Agent, User

logger = logging.getLogger("crm-analytics-service")

class CRMAnalyticsService:
    @staticmethod
    def get_dashboard_stats(db: Session, workspace_id: str, agent_id: str = None):
        avg_duration = db.query(func.avg(Communication.duration)).filter(Communication.workspace_id == workspace_id)
        if agent_id: avg_duration = avg_duration.filter(Communication.agent_id == agent_id)
        
        return {
            "total_revenue": 124592.0,
            "active_voice_agents": 1403,
            "total_subscribers": db.query(Customer).filter(Customer.workspace_id == workspace_id).count(),
            "avg_session_duration": avg_duration.scalar() or 0.0
        }

    @staticmethod
    def get_recent_activity(db: Session, workspace_id: str, limit: int = 5, agent_id: str = None):
        activities = []
        customers = db.query(Customer).filter(Customer.workspace_id == workspace_id).order_by(desc(Customer.updated_at)).limit(limit).all()
        for c in customers:
            activities.append({"type": "new_customer", "title": "New Customer", "description": f"{c.first_name} {c.last_name}", "timestamp": c.updated_at})
        
        comms = db.query(Communication).filter(Communication.workspace_id == workspace_id)
        if agent_id: comms = comms.filter(Communication.agent_id == agent_id)
        for comm in comms.order_by(desc(Communication.started_at)).limit(limit).all():
            activities.append({"type": "communication", "title": f"New {comm.type.capitalize()}", "description": comm.summary or "No summary", "timestamp": comm.started_at})
            
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]

    @staticmethod
    def get_customer_analytics(db: Session, customer_id: str, workspace_id: str, period_type: str = "month", period_value: str = None):
        from dateutil.relativedelta import relativedelta
        # Date resolution logic
        now = datetime.now()
        if period_type == "month":
            year, month = map(int, (period_value or now.strftime("%Y-%m")).split("-"))
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
        else:
            year = int(period_value or now.year)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
        comms = db.query(Communication).filter(
            Communication.workspace_id == workspace_id, Communication.customer_id == customer_id,
            Communication.started_at >= start_date, Communication.started_at <= end_date
        ).all()
        
        agent_stats = {}
        for comm in comms:
            aid = comm.agent_id or "unknown"
            if aid not in agent_stats:
                agent_stats[aid] = {
                    "chat": {"total_messages": 0, "sentiments": []},
                    "phone": {"total_calls": 0, "durations": [], "sentiments": []}
                }
            s = agent_stats[aid]
            if comm.type == "call":
                s["phone"]["total_calls"] += 1
                if comm.duration: s["phone"]["durations"].append(comm.duration)
                if comm.sentiment: s["phone"]["sentiments"].append(comm.sentiment)
            else:
                s["chat"]["total_messages"] += 1
                if comm.sentiment: s["chat"]["sentiments"].append(comm.sentiment)

        return agent_stats
