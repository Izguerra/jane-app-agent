from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.models_db import Customer, Communication, Workspace, Agent
from datetime import datetime, timedelta, timezone
from backend.database import generate_customer_id
import os

class CRMService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, workspace_id: str, agent_id: str = None):
        """Aggregate high-level metrics for the CRM dashboard."""
        
        # 1. Total Revenue (Mocked for MVP as we don't have real stripe data tables fully linked yet)
        # In a real scenario, this would sum up subscription values or invoice totals.
        total_revenue = 124592.00 # Placeholder from mockups
        
        # 2. Active Voice Agents (Count of Agents? Or specific usage?)
        # Let's count active agents in this workspace (usually 1 per workspace, but maybe across the team?)
        # For the dashboard "Active Voice Agents" card, this might imply a platform admin view.
        # But assuming this is a User's CRM for THEIR customers:
        # It might mean "Active Customers using Voice".
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
        # For MVP, we'll return recent Customers added and Integrations activated.
        # This is a bit of a "Fake Feed" for now until we have an 'ActivityLog' table.
        
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

    def get_customers(self, workspace_id: str, skip: int = 0, limit: int = 10, search: str = None):
        """Fetch paginated list of customers, excluding owner/admin users."""
        from backend.models_db import User
        from sqlalchemy import or_, and_
        
        # Query customers for this workspace
        query = self.db.query(Customer).filter(
            Customer.workspace_id == workspace_id,
            Customer.status.notin_(['converted', 'deleted'])
        )
        
        if search:
            search_filt = f"%{search}%"
            query = query.filter(
                (Customer.first_name.ilike(search_filt)) | 
                (Customer.last_name.ilike(search_filt)) | 
                (Customer.email.ilike(search_filt))
            )
            
        total = query.count()
        query = query.order_by(desc(Customer.created_at))
        items = query.offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}

    def create_customer(self, workspace_id: str, data: dict):
        """
        Create a new customer, OR update existing one.
        STRICT PRIORITY: 
        1. Email Match (Primary Identifier)
        2. Phone Match (Secondary, only if no Email or Email not matched yet)
        """
        from sqlalchemy import or_, func
        from backend.models_db import Communication, Appointment
        
        email = data.get("email")
        # Ensure email is stripped/lowercased if present
        if email: email = email.strip().lower()
        
        phone = data.get("phone")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        existing_customer = None
        
        # 1. PRIMARY CHECK: Email
        # If email is provided, it is the SOURCE OF TRUTH.
        if email:
            existing_customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                func.lower(Customer.email) == email,
                Customer.status.notin_(['converted', 'deleted'])
            ).first()
            
        if existing_customer:
            print(f"DEBUG: Found existing customer {existing_customer.id} by EMAIL: {email}")

        # 2. If NOT found, Create New
        # (Phone lookup removed per strict email-only requirement)

        # If found, UPDATE and RETURN
        if existing_customer:
            print(f"DEBUG: Updating existing customer {existing_customer.id}...")
            # Update fields if new data provided and different
            if first_name and first_name.lower() != (existing_customer.first_name or "").lower(): 
                 existing_customer.first_name = first_name
            if last_name and last_name.lower() != (existing_customer.last_name or "").lower():
                 existing_customer.last_name = last_name
            
            # If we found by Phone, but now have Email, update it
            if email and not existing_customer.email:
                 existing_customer.email = email
            elif email and existing_customer.email and existing_customer.email.lower() != email:
                 # WARNING: Email mismatch on Phone match. 
                 # This implies two people share a phone, OR data drift. 
                 # Since Email is Primary, we should technically have found them by Email step 1 if it matched.
                 # So this means: Phone matches User A, but provided Email is new/different.
                 # Policy: Update the record? Or Reject?
                 # Prompt request: "duplicate validation check... duplicate email addresses"
                 # If we update, we don't create duplicate. 
                 print(f"DEBUG: Updating email for customer {existing_customer.id} from {existing_customer.email} to {email}")
                 existing_customer.email = email

            # Update phone if provided
            if phone and phone != existing_customer.phone:
                 existing_customer.phone = phone
            
            # Update other fields
            if data.get("plan"): existing_customer.plan = data.get("plan")
            if data.get("lifecycle_stage"): existing_customer.lifecycle_stage = data.get("lifecycle_stage")
            if data.get("crm_status"): existing_customer.crm_status = data.get("crm_status")
            
            self.db.commit()
            self.db.refresh(existing_customer)
            return existing_customer

        # 3. If NOT found, Create New
        # FINAL CHECK: Ensure we didn't miss an email (redundant but safe)
        if email:
             double_check = self.db.query(Customer).filter(
                 Customer.workspace_id == workspace_id,
                 func.lower(Customer.email) == email,
                 Customer.status.notin_(['converted', 'deleted'])
             ).first()
             if double_check:
                 return double_check

        customer = Customer(
            id=generate_customer_id(),
            workspace_id=workspace_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            status=data.get("status", "active"),
            plan=data.get("plan", "Starter"),
            usage_limit=data.get("usage_limit", 1000),
            usage_used=data.get("usage_used", 0),
            lifecycle_stage=data.get("lifecycle_stage"),
            crm_status=data.get("crm_status"),
            customer_type=data.get("customer_type")
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_customer_by_id(self, workspace_id: str, customer_id: str):
        """Get a single customer by ID."""
        return self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id
        ).first()

    def get_customer_communications(self, customer_id: str, limit: int = 10, offset: int = 0, type: str = None):
        """Get communications for a specific customer."""
        # Link communications to customers via customer_id field or workspace scope
        query = self.db.query(Communication).filter(
            Communication.workspace_id.in_(
                self.db.query(Customer.workspace_id).filter(Customer.id == customer_id)
            )
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

    def get_customer_analytics(self, customer_id: str, workspace_id: str, period_type: str = "month", period_value: str = None):
        """Get customer analytics grouped by agent with time period filtering."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        import calendar
        
        # Determine date range based on period
        if period_value is None:
            now = datetime.now()
            if period_type == "month":
                period_value = now.strftime("%Y-%m")
            else:  # year
                period_value = str(now.year)
        
        if period_type == "month":
            # Parse YYYY-MM
            year, month = map(int, period_value.split("-"))
            start_date = datetime(year, month, 1)
            # Last day of month
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
                
                # Use real sentiment if available
                if comm.sentiment:
                    stats["chat"]["sentiments"].append(comm.sentiment)
                
            elif comm.type == "call":
                stats["phone"]["total_calls"] += 1
                if comm.duration:
                    stats["phone"]["durations"].append(comm.duration)
                
                # Use real sentiment if available
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
        from backend.models_db import Appointment
        appointments = self.db.query(Appointment).filter(
            Appointment.customer_id == customer_id,
            Appointment.workspace_id == workspace_id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date
        ).all()
        
        for appt in appointments:
            # Since appointments don't have an agent_id yet, attribute to 'unknown' or the most active agent?
            # For now, let's use 'unknown' to be safe, or if we want to bundle with primary:
            # But primary isn't determined until later. So 'unknown' or a fallback is best.
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
            # appt.appointment_date is timezone aware?
            now = datetime.now(appt.appointment_date.tzinfo) if appt.appointment_date.tzinfo else datetime.now()
            if appt.appointment_date > now:
                stats["appointments"]["upcoming"] += 1
            elif appt.status == 'completed':
                stats["appointments"]["completed"] += 1
            
            # Add to recent activity?
            stats["recent_activity"].append({
                "date": appt.appointment_date.strftime("%Y-%m-%d"),
                "count": 1
            })

        # Calculate aggregated stats and format response
        result_agents = []
        
        # Lazy import User to avoid circular dependency
        from backend.models_db import User
        
        for agent_id, stats in agent_stats.items():
            # Get agent info - try Agent table first, then User table
            agent_name = "Unknown Agent"
            agent_avatar = None
            
            if agent_id and agent_id != "unknown":
                agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    agent_name = agent.name
                    # agent_avatar = agent.avatar_url 
                else:
                    # Try User table (human agents)
                    user = self.db.query(User).filter(User.id == agent_id).first()
                    if user:
                        agent_name = user.name or f"{user.first_name} {user.last_name}"
            elif agent_id == "unknown":
                # Fallback to the default agent for this workspace
                # Usually there is one main AI agent per workspace
                default_agent = self.db.query(Agent).filter(
                    Agent.workspace_id == workspace_id
                    # Could add is_active=True or similar if needed
                ).first()
                
                if default_agent:
                    agent_name = default_agent.name
                    # agent_id = default_agent.id # Do we merge stats? 
                    # If we merge stats, we need to restructure the dictionary which is hard here.
                    # For now, just label it correctly.
                    # Ideally we would have merged these earlier, but simple display fix is safer.
            
            # Calculate chat aggregates
            chat_stats = {
                "total_messages": stats["chat"]["total_messages"],
                "total_conversations": stats["chat"]["total_conversations"],
                "avg_response_time_seconds": 0, # Not tracking response time yet
                "satisfaction_rating": 0, # Not tracking ratings yet
                "sentiment": self._calculate_sentiment_breakdown(stats["chat"]["sentiments"]),
                "platforms": {}
            }
            
            # Platform-specific stats
            for platform, platform_stats in stats["chat"]["platforms"].items():
                chat_stats["platforms"][platform] = {
                    "messages": platform_stats["messages"],
                    "conversations": platform_stats["conversations"],
                    "avg_response_time_seconds": 0
                }
            
            # Calculate phone aggregates
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
            
            # Aggregate recent activity by date
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
                    "recent_activity": recent_activity[-30:]  # Last 30 days
                }
            })
        
        # Sort by total interactions (primary agent first)
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

    def get_customer_appointments(self, customer_id: str, limit: int = 10, offset: int = 0):
        """Get appointments for a specific customer."""
        from backend.models_db import Appointment
        
        query = self.db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        ).order_by(desc(Appointment.appointment_date))
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return {"items": items, "total": total}

    def get_customer_campaigns(self, customer_id: str, limit: int = 10, offset: int = 0):
        """Get campaigns a customer is enrolled in."""
        from backend.models_db import Campaign, CampaignEnrollment, Communication
        
        # Query Enrollments
        query = self.db.query(CampaignEnrollment, Campaign).join(
            Campaign, CampaignEnrollment.campaign_id == Campaign.id
        ).filter(
            CampaignEnrollment.customer_id == customer_id
        ).order_by(desc(CampaignEnrollment.created_at))
        
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        items = []
        for enrollment, campaign in results:
            # Try to find response?
            # Ideally we'd look for latest inbound communication linked to this campaign?
            # For now, keep it simple.
            
            items.append({
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_status": "active" if campaign.is_active else "paused", # Mapping boolean to string status
                "enrolled_at": enrollment.created_at,
                "contacted_at": enrollment.last_run_at or enrollment.created_at,
                "status": enrollment.status,
                "current_step": enrollment.current_step_order,
                "next_run_at": enrollment.next_run_at,
                "response_type": None, # Complex to resolve mapping back strictly
            })
                
        return {"items": items, "total": total}

    def get_customer_voice_calls(self, customer_id: str, limit: int = 20, offset: int = 0):
        """Get voice calls for a specific customer."""
        query = self.db.query(Communication).filter(
            Communication.workspace_id.in_(
                self.db.query(Customer.workspace_id).filter(Customer.id == customer_id)
            ),
            Communication.type == 'call'
        ).order_by(desc(Communication.started_at))
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        return {"items": items, "total": total}


    def analyze_and_update_customer_status(self, customer_id: str, interaction_text: str, interaction_type: str = "chat"):
        """
        Analyze an interaction using LLM to update customer CRM status and lifecycle stage.
        """
        import os
        import json
        
        # 1. Fetch Customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "error": "Customer not found"}

        # 2. Prepare Context (Current State)
        current_state = {
            "customer_type": customer.customer_type,
            "lifecycle_stage": customer.lifecycle_stage,
            "crm_status": customer.crm_status,
            "account_status": customer.status
        }
        
        # 3. Construct Prompt
        prompt = f"""
        You are an expert CRM manager. Analyze the following customer interaction and determine if the customer's classification should be updated.
        
        Current Customer State:
        {json.dumps(current_state, indent=2)}
        
        New Interaction ({interaction_type}):
        "{interaction_text}"
        
        Rules for Classification:
        1. Lifecycle Stage:
           - Subscriber: Just signed up, no interaction.
           - Lead: Engaged in chat, asked general questions.
           - MQL (Marketing Qualified Lead): Asked specific questions about features, pricing, or use cases.
           - SQL (Sales Qualified Lead): Requested a demo, quote, or meeting.
           - Opportunity: Appointment booked or negotiation started.
           - Customer: Completed purchase or payment.
           - Evangelist: Positive feedback, referrals.
           
        2. CRM Status (Interaction Status):
           - New/Raw: No contact yet.
           - Attempted to Contact: specific outreach made (outbound).
           - Working/Contacted: Active conversation.
           - Nurture: Interested but not ready (e.g., "ask me later").
           - Bad Fit: Explicitly not interested or wrong profile.
           - At Risk: Negative sentiment, complaints, "cancel" mentioned.
           - Active: Normal healthy interaction.
           
        3. Customer Type:
           - B2B: Mentions company, team, enterprise needs.
           - B2C: Personal use, individual email.
        
        Return ONLY a valid JSON object with keys: "lifecycle_stage", "crm_status", "customer_type". 
        If a field should NOT change from its current state (or if there is insufficient info to change it), set it to null.
        Do strictly adhere to the allowed values if possible (lowercase/snake_case preferred for db storage).
        """
        
        try:
            from backend.lib.ai_client import get_ai_client
            client, model_name = get_ai_client(workspace_id=customer.workspace_id, async_mode=False)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a CRM AI assistant. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # 4. Apply Updates
            updates_made = False
            changes = {}
            
            # Helper to normalize and check changes
            def update_if_changed(field, new_val):
                current_val = getattr(customer, field)
                # Only update if new_val is not None/Empty and different from current
                if new_val and new_val.lower() != (current_val or "").lower():
                    setattr(customer, field, new_val.lower()) # Store as lowercase for consistency
                    return True
                return False

            if result.get("lifecycle_stage"):
                if update_if_changed("lifecycle_stage", result["lifecycle_stage"]):
                    changes["lifecycle_stage"] = result["lifecycle_stage"]
                    updates_made = True
            
            if result.get("crm_status"):
                if update_if_changed("crm_status", result["crm_status"]):
                    changes["crm_status"] = result["crm_status"]
                    updates_made = True
                
            if result.get("customer_type"):
                if update_if_changed("customer_type", result["customer_type"]):
                    changes["customer_type"] = result["customer_type"]
                    updates_made = True
            
            if updates_made:
                self.db.commit()
                self.db.refresh(customer)
                
            return {"success": True, "updates": changes, "changed": updates_made, "analysis": result}
            
        except Exception as e:
            print(f"Error in CRM analysis: {e}")
            return {"success": False, "error": str(e)}

    def ensure_customer_from_interaction(self, workspace_id: str, identifier: str, channel: str, name: str = None):
        """
        Ensure a customer record exists for the given identifier (email or phone).
        Delegates to get_or_create_from_identifier for resolution logic.
        Updates last_contact_date.
        """
        from datetime import datetime, timezone
        
        customer = self.get_or_create_from_identifier(workspace_id, identifier, channel, name)
        
        if customer:
            # Update last contact date
            customer.last_contact_date = datetime.now(timezone.utc)
            self.db.commit()
            
        return customer


    def update_status_on_appointment(self, workspace_id: str, customer_id: str):
        """
        Upgrade customer status when an appointment is booked.
        Uses the standardized convert_to_customer method.
        """
        try:
            self.convert_to_customer(
                customer_id=customer_id,
                conversion_trigger="appointment"
            )
            print(f"DEBUG: Upgraded customer {customer_id} to Customer due to Appointment.")
            return True
        except Exception as e:
            print(f"Error upgrading customer on appointment: {e}")
            return False

    def convert_to_customer(self, customer_id: str, conversion_trigger: str):
        """
        Convert a Guest/Lead to a full Customer.
        - Generates cust_id
        - Updates customer_type to 'customer'
        - Sets converted_at timestamp
        """
        from backend.database import generate_customer_id
        from datetime import datetime, timezone

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # If already a customer, just return (idempotent)
        if customer.customer_type == "customer":
            return customer

        # Perform conversion
        if not customer.cust_id:
            customer.cust_id = generate_customer_id()
        
        customer.customer_type = "customer"
        customer.lifecycle_stage = "Customer"
        customer.crm_status = "Active"
        customer.converted_at = datetime.now(timezone.utc)
        customer.converted_by = conversion_trigger
        
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def promote_guest_to_customer(self, guest_id: str, new_email: str = None, new_phone: str = None, new_name: str = None):
        """
        DEPRECATED: Use convert_to_customer instead.
        Kept for backward compatibility but redirected to new logic.
        """
        # If new info provided, update it first
        if new_email or new_phone or new_name:
            customer = self.db.query(Customer).filter(Customer.id == guest_id).first()
            if customer:
                if new_email: customer.email = new_email
                if new_phone: customer.phone = new_phone
                if new_name:
                    parts = new_name.split(" ", 1)
                    customer.first_name = parts[0]
                    if len(parts) > 1: customer.last_name = parts[1]
                self.db.commit()

        return self.convert_to_customer(guest_id, "admin_action")

    def get_or_create_from_identifier(self, workspace_id: str, identifier: str, channel: str = "phone", name: str = None) -> Customer:
        """
        Find or create a customer/guest.
        Lookup priority:
        1. Session ID (ann_...)
        2. Phone number (normalized)
        3. Email address
        """
        from backend.database import generate_guest_id, format_session_id
        
        if not identifier:
            return None
            
        # 1. CHECK SESSION ID (Strongest for anonymous)
        if identifier.startswith("ann_"):
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.session_id == identifier,
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer
                
            # If not found but is session ID, create new guest linked to this session
            return self._create_guest(workspace_id, session_id=identifier, channel=channel, name=name)

        # 2. CLEAN IDENTIFIER FOR CONTACT LOOKUP
        clean_id = identifier.replace("sip:", "").replace("whatsapp:", "").strip()
        is_email = "@" in clean_id
        
        if is_email:
            clean_id = clean_id.lower()
            
            # Check Email
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                func.lower(Customer.email) == clean_id,
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer
                
        else:
            # Check Phone (with normalization)
            digits_only = "".join(filter(str.isdigit, clean_id))
            search_values = {clean_id}
            if digits_only:
                search_values.add(digits_only)
                search_values.add(f"+{digits_only}")
                if len(digits_only) == 10:
                    search_values.add(f"1{digits_only}")
                if len(digits_only) == 11 and digits_only.startswith("1"):
                    search_values.add(digits_only[1:])
            
            customer = self.db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.phone.in_(search_values),
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer

        # 3. CREATE NEW GUEST (if no match)
        return self._create_guest(workspace_id, identifier_val=clean_id, is_email=is_email, channel=channel, name=name)

    def _create_guest(self, workspace_id: str, session_id: str = None, identifier_val: str = None, is_email: bool = False, channel: str = "web", name: str = None):
        from backend.database import generate_guest_id
        
        guest_id = generate_guest_id()
        first_name = "Guest"
        last_name = "User"
        
        if name:
             parts = name.split(" ", 1)
             first_name = parts[0]
             if len(parts) > 1:
                 last_name = parts[1]
        
        guest = Customer(
            id=guest_id,
            workspace_id=workspace_id,
            first_name=first_name,
            last_name=last_name,
            status="active",
            customer_type="guest",
            session_id=session_id
        )
        
        if identifier_val:
            if is_email:
                guest.email = identifier_val
            else:
                guest.phone = identifier_val
                
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def cleanup_stale_sessions(self, workspace_id: str):
        """
        Close sessions that have been idle for too long.
        - Chat/Text: 2 minutes (Strict User Requirement)
        - Voice/Call: 2 minutes (Strict User Requirement)
        """
        from datetime import datetime, timedelta, timezone
        
        # 1. Close stale CHAT sessions (idle for 2 minutes)
        # Fix: Check for RECENT messages, not just started_at
        from backend.models_db import ConversationMessage
        
        chat_cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
        
        # Find ongoing chat sessions
        active_chats = self.db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.status == 'ongoing',
            Communication.type == 'chat'
        ).all()
        
        chats_closed = 0
        for chat in active_chats:
            # Check last message time
            last_msg = self.db.query(ConversationMessage).filter(
                ConversationMessage.communication_id == chat.id
            ).order_by(desc(ConversationMessage.created_at)).first()
            
            last_activity = last_msg.created_at if last_msg else chat.started_at
            
            # If naive, assume UTC or ensure comparison works (created_at is server_default=func.now(), usually naive UTC in some setups, but better be safe)
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
                
            if last_activity < chat_cutoff:
                chat.status = "completed"
                chat.ended_at = datetime.now(timezone.utc)
                chat.call_outcome = "Session Timeout"
                chats_closed += 1
        
        # 2. Close stale VOICE sessions (2 minute cutoff for starting, but let's add a 1-hour hard cap for safety)
        # If the call was started more than 1 hour ago and is still 'ongoing', it's likely a zombie.
        # If it was started > 2 mins ago, it *might* be stale if it's just a preview, 
        # but let's honor the "2 minute" requirement strictly for now while adding logging.
        voice_cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
        hard_cap_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # We'll use a granular query to log exactly which sessions we are closing
        stale_voice_sessions = self.db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.status == 'ongoing',
            Communication.type == 'call',
            Communication.started_at < voice_cutoff
        ).all()
        
        voice_updated = 0
        for session in stale_voice_sessions:
            session.status = "completed"
            session.ended_at = datetime.now(timezone.utc)
            session.call_outcome = "Session Timeout (Stale)"
            voice_updated += 1
            print(f"DEBUG: Closing stale VOICE session {session.id} (Started: {session.started_at})")
        
        if chats_closed > 0 or voice_updated > 0:
            self.db.commit()
            print(f"DEBUG: [CLEANUP] Workspace {workspace_id}: Closed {chats_closed} chat(s) and {voice_updated} voice session(s).")

def run_session_cleanup(workspace_id: str):
    """
    Helper to run cleanup in background tasks where DB session requires management.
    """
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        service = CRMService(db)
        service.cleanup_stale_sessions(workspace_id)
    except Exception as e:
        print(f"Error in background session cleanup: {e}")
    finally:
        db.close()
