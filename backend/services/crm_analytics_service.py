from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
import calendar
from backend.models_db import Customer, Communication, Appointment, CampaignEnrollment, Campaign, Agent, User

class CRMAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_workspace_usage_stats(self, workspace_id: str, start_date: datetime = None, end_date: datetime = None):
        """Aggregate usage stats (conversations, voice minutes) for a workspace."""
        filters = [Communication.workspace_id == workspace_id]
        
        if start_date:
            filters.append(Communication.started_at >= start_date)
        if end_date:
            filters.append(Communication.started_at <= end_date)
            
        # Total conversations (all types)
        total_conversations = self.db.query(func.count(Communication.id)).filter(*filters).scalar() or 0
        
        # Voice minutes (only calls)
        voice_seconds = self.db.query(func.sum(Communication.duration)).filter(
            *filters, 
            Communication.type == 'call'
        ).scalar() or 0
        
        return {
            "conversations_count": total_conversations,
            "voice_minutes_used": round(voice_seconds / 60, 2)
        }

    def get_dashboard_stats(self, workspace_id: str, agent_id: str = None):
        """Aggregate high-level metrics for the CRM dashboard."""
        
        # 1. Total Revenue (Mocked for MVP as we don't have real stripe data tables fully linked yet)
        total_revenue = 124592.00 # Placeholder from mockups
        
        # 2. Active Voice Agents Or Active Customers
        active_voice_agents = 1403 # Placeholder
        
        # 3. Total Subscribers (Count of Customers)
        total_subscribers = self.db.query(Customer).filter(
            Customer.workspace_id == workspace_id
        ).count()
        
        # 4. Avg Session Duration
        avg_duration_query = self.db.query(func.avg(Communication.duration)).filter(
            Communication.workspace_id == workspace_id
        )
        if agent_id:
             avg_duration_query = avg_duration_query.filter(Communication.agent_id == agent_id)
             
        avg_duration = avg_duration_query.scalar() or 0.0
        
        return {
            "total_revenue": total_revenue,
            "active_voice_agents": active_voice_agents,
            "total_subscribers": total_subscribers,
            "avg_session_duration": avg_duration
        }

    def get_recent_activity(self, workspace_id: str, limit: int = 5, agent_id: str = None):
        """Fetch a mixed stream of recent events."""
        activities = []
        
        # Recent Customers
        recent_customers = self.db.query(Customer).filter(
            Customer.workspace_id == workspace_id
        ).order_by(desc(Customer.updated_at)).limit(limit).all()
        
        for c in recent_customers:
            activities.append({
                "type": "new_customer",
                "title": "New Customer Added",
                "description": f"{c.first_name} {c.last_name}",
                "timestamp": c.updated_at
            })
            
        # Recent Communications (as a proxy for "Activity")
        recent_comms_query = self.db.query(Communication).filter(
            Communication.workspace_id == workspace_id
        )
        if agent_id:
            recent_comms_query = recent_comms_query.filter(Communication.agent_id == agent_id)
            
        recent_comms = recent_comms_query.order_by(desc(Communication.started_at)).limit(limit).all()
        
        for comm in recent_comms:
            activities.append({
                "type": "communication",
                "title": f"New {comm.type.capitalize()}",
                "description": comm.summary or "No summary available",
                "timestamp": comm.started_at
            })
            
        # Sort combined list
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]

    def get_customer_communications(self, customer_id: str, limit: int = 10, offset: int = 0, type: str = None):
        """Get communications for a specific customer."""
        # Link communications to customers via customer_id field
        query = self.db.query(Communication).filter(
            Communication.customer_id == customer_id,
            Communication.workspace_id == self.db.query(Customer.workspace_id).filter(Customer.id == customer_id).scalar_subquery()
        )
        
        if type:
            if type == 'voice': # Frontend sends 'voice', backend stores 'call'
                query = query.filter(Communication.type == 'call')
            else:
                query = query.filter(Communication.type == type)
                
        query = query.order_by(desc(Communication.started_at))
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return {"items": items, "total": total}

    def get_customer_voice_calls(self, customer_id: str, limit: int = 20, offset: int = 0):
        """Get voice calls for a specific customer."""
        query = self.db.query(Communication).filter(
            Communication.customer_id == customer_id,
            Communication.type == 'call'
        ).order_by(desc(Communication.started_at))
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return {"items": items, "total": total}

    def get_customer_appointments(self, customer_id: str, limit: int = 10, offset: int = 0):
        """Get appointments for a specific customer."""
        query = self.db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        ).order_by(desc(Appointment.appointment_date))
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return {"items": items, "total": total}

    def get_customer_campaigns(self, customer_id: str, limit: int = 10, offset: int = 0):
        """Get campaigns a customer is enrolled in."""
        query = self.db.query(CampaignEnrollment, Campaign).join(
            Campaign, CampaignEnrollment.campaign_id == Campaign.id
        ).filter(
            CampaignEnrollment.customer_id == customer_id
        ).order_by(desc(CampaignEnrollment.created_at))
        
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        items = []
        for enrollment, campaign in results:
            items.append({
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_status": "active" if campaign.is_active else "paused",
                "enrolled_at": enrollment.created_at,
                "contacted_at": enrollment.last_run_at or enrollment.created_at,
                "status": enrollment.status,
                "current_step": enrollment.current_step_order,
                "next_run_at": enrollment.next_run_at,
                "response_type": None,
            })
                
        return {"items": items, "total": total}

    def get_customer_analytics(self, customer_id: str, workspace_id: str, period_type: str = "month", period_value: str = None):
        """Get customer analytics grouped by agent with time period filtering."""
        
        # Determine date range based on period
        if period_value is None:
            now = datetime.now()
            if period_type == "month":
                period_value = now.strftime("%Y-%m")
            else:  # year
                period_value = str(now.year)
        
        if period_type == "month":
            year, month = map(int, period_value.split("-"))
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59)
        else:  # year
            year = int(period_value)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
        
        # Get all communications for this customer in the period
        communications = self.db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.customer_id == customer_id,
            Communication.started_at >= start_date,
            Communication.started_at <= end_date
        ).all()
        
        # Group by agent
        agent_stats = {}
        
        for comm in communications:
            agent_id = comm.agent_id or "unknown"
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "chat": {"platforms": {}, "total_messages": 0, "total_conversations": 0, "response_times": [], "ratings": [], "sentiments": []},
                    "phone": {"total_calls": 0, "durations": [], "ratings": [], "sentiments": []},
                    "appointments": {"total_booked": 0, "upcoming": 0, "completed": 0},
                    "status_breakdown": {"completed": 0, "failed": 0, "ongoing": 0},
                    "recent_activity": []
                }
            
            stats = agent_stats[agent_id]
            
            # Categorize by type
            if comm.type in ["chat", "whatsapp", "instagram", "facebook"]:
                platform = comm.type
                if platform not in stats["chat"]["platforms"]:
                    stats["chat"]["platforms"][platform] = {"messages": 0, "conversations": 0, "response_times": []}
                
                stats["chat"]["platforms"][platform]["messages"] += 1
                stats["chat"]["platforms"][platform]["conversations"] += 1
                stats["chat"]["total_messages"] += 1
                stats["chat"]["total_conversations"] += 1
                
                if comm.sentiment:
                    stats["chat"]["sentiments"].append(comm.sentiment)
                
            elif comm.type == "call":
                stats["phone"]["total_calls"] += 1
                if comm.duration:
                    stats["phone"]["durations"].append(comm.duration)
                
                if comm.sentiment:
                    stats["phone"]["sentiments"].append(comm.sentiment)
            
            # Status breakdown
            if comm.status in stats["status_breakdown"]:
                stats["status_breakdown"][comm.status] += 1
            
            # Recent activity
            stats["recent_activity"].append({
                "date": comm.started_at.strftime("%Y-%m-%d"),
                "count": 1
            })
            
        # Get appointments for this customer in the period
        appointments = self.db.query(Appointment).filter(
            Appointment.customer_id == customer_id,
            Appointment.workspace_id == workspace_id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date
        ).all()
        
        for appt in appointments:
            agent_id = "unknown"
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "chat": {"platforms": {}, "total_messages": 0, "total_conversations": 0, "response_times": [], "ratings": [], "sentiments": []},
                    "phone": {"total_calls": 0, "durations": [], "ratings": [], "sentiments": []},
                    "appointments": {"total_booked": 0, "upcoming": 0, "completed": 0},
                    "status_breakdown": {"completed": 0, "failed": 0, "ongoing": 0},
                    "recent_activity": []
                }
            
            stats = agent_stats[agent_id]
            stats["appointments"]["total_booked"] += 1
            
            # Check if upcoming
            now = datetime.now(appt.appointment_date.tzinfo) if appt.appointment_date.tzinfo else datetime.now()
            if appt.appointment_date > now:
                stats["appointments"]["upcoming"] += 1
            elif appt.status == 'completed':
                stats["appointments"]["completed"] += 1
            
            # Add to recent activity
            stats["recent_activity"].append({
                "date": appt.appointment_date.strftime("%Y-%m-%d"),
                "count": 1
            })

        # Calculate aggregated stats and format response
        result_agents = []
        
        for agent_id, stats in agent_stats.items():
            agent_name = "Unknown Agent"
            agent_avatar = None
            
            if agent_id and agent_id != "unknown":
                agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    agent_name = agent.name
                else:
                    user = self.db.query(User).filter(User.id == agent_id).first()
                    if user:
                        agent_name = user.name or f"{user.first_name} {user.last_name}"
            elif agent_id == "unknown":
                default_agent = self.db.query(Agent).filter(
                    Agent.workspace_id == workspace_id
                ).first()
                
                if default_agent:
                    agent_name = default_agent.name
            
            chat_stats = {
                "total_messages": stats["chat"]["total_messages"],
                "total_conversations": stats["chat"]["total_conversations"],
                "avg_response_time_seconds": 0,
                "satisfaction_rating": 0,
                "sentiment": self._calculate_sentiment_breakdown(stats["chat"]["sentiments"]),
                "platforms": {}
            }
            
            for platform, platform_stats in stats["chat"]["platforms"].items():
                chat_stats["platforms"][platform] = {
                    "messages": platform_stats["messages"],
                    "conversations": platform_stats["conversations"],
                    "avg_response_time_seconds": 0
                }
            
            phone_avg_duration = 0
            if stats["phone"]["durations"]:
                phone_avg_duration = int(sum(stats["phone"]["durations"]) / len(stats["phone"]["durations"]))
                
            phone_stats = {
                "total_calls": stats["phone"]["total_calls"],
                "total_duration_seconds": sum(stats["phone"]["durations"]),
                "avg_duration_seconds": phone_avg_duration,
                "satisfaction_rating": 0,
                "sentiment": self._calculate_sentiment_breakdown(stats["phone"]["sentiments"])
            }
            
            activity_by_date = {}
            for activity in stats["recent_activity"]:
                date = activity["date"]
                activity_by_date[date] = activity_by_date.get(date, 0) + activity["count"]
            
            recent_activity = [{"date": date, "count": count} for date, count in sorted(activity_by_date.items())]
            
            result_agents.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "avatar_url": agent_avatar,
                "stats": {
                    "chat": chat_stats,
                    "phone": phone_stats,
                    "appointments": stats["appointments"],
                    "status_breakdown": stats["status_breakdown"],
                    "recent_activity": recent_activity[-30:]
                }
            })
        
        result_agents.sort(key=lambda x: x["stats"]["chat"]["total_messages"] + x["stats"]["phone"]["total_calls"], reverse=True)
        
        return {
            "primary_agent": result_agents[0] if result_agents else None,
            "additional_agents": result_agents[1:] if len(result_agents) > 1 else []
        }
    
    def _calculate_sentiment_breakdown(self, sentiments):
        if not sentiments:
            return {"positive": 0, "neutral": 0, "negative": 0}
            
        total = len(sentiments)
        positive = sentiments.count("positive")
        neutral = sentiments.count("neutral")
        negative = sentiments.count("negative")
        
        return {
            "positive": round((positive / total) * 100),
            "neutral": round((neutral / total) * 100),
            "negative": round((negative / total) * 100)
        }
