from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB as PG_JSONB
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

# Dialect-agnostic types for unit testing compatibility (SQLite)
JSONB = JSON().with_variant(PG_JSONB(), "postgresql")

def ARRAY(item_type):
    """Return a type that is ARRAY in Postgres and Text/JSON in SQLite."""
    return JSON().with_variant(PG_ARRAY(item_type), "postgresql")


# Handle both import contexts (uvicorn vs direct execution)
try:
    from backend.database import Base
except ModuleNotFoundError:
    from database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    plan_name = Column(String(50), nullable=True) # 'Starter', 'Professional', etc.
    subscription_status = Column(String(50), nullable=True) # 'active', 'trialing', etc.
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_product_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    team_id = Column(String(50), ForeignKey("teams.id"), nullable=False)
    role = Column(String(50), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(String(50), primary_key=True, index=True)
    team_id = Column(String(50), ForeignKey("teams.id"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    action = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)

class PlatformIntegration(Base):
    __tablename__ = "platform_integrations"
    
    id = Column(String(50), primary_key=True, index=True)
    provider = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AdminSetting(Base):
    __tablename__ = "admin_settings"
    
    id = Column(Integer, primary_key=True) # Singleton row, usually id=1
    company_name = Column(String(255), default="SupaAgent Inc.")
    support_email = Column(String(255), default="support@supaagent.com")
    default_language = Column(String(10), default="en-US")
    timezone = Column(String(50), default="America/New_York")
    two_factor_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(50), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ActiveSession(Base):
    __tablename__ = "active_sessions"
    
    id = Column(String(255), primary_key=True) # Session ID
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    first_name = Column(String(50), nullable=True) # Added
    last_name = Column(String(50), nullable=True) # Added
    username = Column(String(50), unique=True, nullable=True) # Added
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String(50), default="member")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(50), primary_key=True, index=True)
    team_id = Column(String(50), ForeignKey("teams.id"), nullable=False) # Maps to teams.id
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # New columns present in 'workspaces' table
    description = Column(Text, nullable=True)
    services = Column(Text, nullable=True)
    business_hours = Column(Text, nullable=True)
    faq = Column(Text, nullable=True)
    reference_urls = Column(Text, nullable=True)
    conversations_this_month = Column(Integer, default=0)
    voice_minutes_this_month = Column(Integer, default=0)
    inbound_agent_phone = Column(String(50), nullable=True, unique=True)
    
    # Customer lifecycle settings
    churn_threshold_days = Column(Integer, default=90)  # Days of inactivity before marking customer as inactive
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False, default="My Agent")
    voice_id = Column(String(50))
    language = Column(String(10), default="en")
    prompt_template = Column(Text)
    welcome_message = Column(Text, nullable=True)
    soul = Column(Text, nullable=True)
    is_orchestrator = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)
    allowed_worker_types = Column(JSON, default=[]) # List of worker slugs this agent can dispatch
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    phone_numbers = relationship("PhoneNumber", back_populates="agent")


class Communication(Base):
    __tablename__ = "communications"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    type = Column(String(50), nullable=False) # "call" or "chat"
    direction = Column(String(50), nullable=False) # "inbound" or "outbound"
    status = Column(String(50), nullable=False) # "completed", "missed", "failed"
    duration = Column(Integer, default=0)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # New fields for unified history
    channel = Column(String(50), nullable=True) # "whatsapp", "instagram", "facebook", "web", "phone_call"
    integration_id = Column(String(50), ForeignKey("integrations.id"), nullable=True)
    recording_url = Column(Text, nullable=True)
    user_identifier = Column(String(255), nullable=True) # Phone number or handle
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)
    
    # Outbound calling fields
    call_intent = Column(Text, nullable=True)  # "appointment_reminder", "deal_follow_up", "lead_qualification"
    call_outcome = Column(Text, nullable=True)  # "answered", "voicemail", "no_answer", "busy", "failed"
    call_context = Column(JSON, nullable=True)  # JSONB for appointment/deal/campaign data
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=True)
    twilio_call_sid = Column(Text, nullable=True)  # Twilio call SID for tracking
    retry_count = Column(Integer, default=0)
    parent_communication_id = Column(String(50), nullable=True)  # For retry tracking
    campaign_id = Column(Text, nullable=True)
    campaign_name = Column(Text, nullable=True)


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    provider = Column(String(50), nullable=False) 
    credentials = Column(Text, nullable=True) 
    settings = Column(Text, nullable=True) 
    is_active = Column(Boolean, default=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) 
    content_hash = Column(String(64), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    """
    Customer/Client records for workspace owners to track their end-customers.
    
    IMPORTANT: This table is NOT for platform users/subscribers.
    - Platform users are in the 'users' table
    - Each platform user gets their own workspace
    - This table is for workspace owners to track THEIR customers/clients
    - Scoped by workspace_id
    """
    __tablename__ = "customers"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    company_name = Column(String(255), nullable=True) # Company/Business name
    
    # New CRM fields
    status = Column(String(50), default="active", nullable=False) # active, trialing, past_due, churned
    plan = Column(String(50), default="Starter", nullable=True)
    usage_limit = Column(Integer, default=1000) # minutes
    usage_used = Column(Integer, default=0) # minutes
    avatar_url = Column(String(255), nullable=True)
    
    # Advanced CRM fields
    lifecycle_stage = Column(String(50), nullable=True) # Subscriber, Lead, MQL, SQL, Opportunity, Customer, Evangelist, Other
    crm_status = Column(String(50), nullable=True) # New/Raw, Attempted to Contact, Working, Active, etc.
    customer_type = Column(String(50), default="guest", nullable=False) # guest, lead, customer, returning, inactive
    
    # Session & Identity Tracking
    session_id = Column(String(255), nullable=True, index=True)  # ann_... (anonymous session from client)
    cust_id = Column(String(50), nullable=True, unique=True, index=True)  # cust_... (assigned on conversion)
    auth_user_id = Column(String(50), nullable=True, index=True)  # usr_... (if platform-authenticated user)
    
    # Conversion Tracking
    converted_at = Column(DateTime(timezone=True), nullable=True)
    converted_by = Column(String(50), nullable=True)  # appointment, purchase, admin
    
    # Activity Tracking (for churn detection)
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    interaction_count = Column(Integer, default=0)
    
    # Stripe integration fields
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    stripe_payment_method_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), nullable=True)  # active, past_due, canceled, trialing, etc.
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Lead tracking fields
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    lead_source = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    
    # Guest value tracking
    converted_to_id = Column(String(50), nullable=True) # ID of the real customer this guest was converted to
    original_guest_id = Column(String(50), nullable=True) # ID of the guest record this customer came from
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    user_identifier = Column(String(255), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    communication_id = Column(String(50), ForeignKey("communications.id"), nullable=True)


class PhoneNumber(Base):
    """Twilio phone numbers provisioned for workspaces"""
    __tablename__ = "phone_numbers"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String(50), unique=True, nullable=False, index=True)
    friendly_name = Column(String(255), nullable=True)
    country_code = Column(String(2), nullable=True)
    
    # Capabilities
    voice_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    
    # Configuration
    voice_url = Column(Text, nullable=True)
    whatsapp_webhook_url = Column(Text, nullable=True)
    
    # Twilio details
    twilio_sid = Column(String(255), unique=True, nullable=True, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)
    
    # Billing
    stripe_subscription_item_id = Column(String(255), nullable=True)
    monthly_cost = Column(Integer, nullable=True)  # Store as cents
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    
    workspace = relationship("Workspace") # Simplified
    agent = relationship("Agent", back_populates="phone_numbers")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WhatsAppTemplate(Base):
    """WhatsApp message templates for Meta WhatsApp API"""
    __tablename__ = "whatsapp_templates"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(10), default="en")
    category = Column(String(50), nullable=True)  # MARKETING, UTILITY, AUTHENTICATION
    status = Column(String(50), nullable=True)    # PENDING, APPROVED, REJECTED
    template_id = Column(String(255), nullable=True)  # Meta template ID
    components = Column(Text, nullable=True)  # JSON string of template structure
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Appointment(Base):
    """Customer appointments for scheduling and reminder calls"""
    __tablename__ = "appointments"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True)  # Made nullable
    
    # Customer contact info (denormalized for easier access)
    customer_first_name = Column(String(100), nullable=True)
    customer_last_name = Column(String(100), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    appointment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    status = Column(Text, nullable=False, default="scheduled")  # scheduled, confirmed, completed, cancelled, no_show
    location = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    calendar_event_id = Column(Text, nullable=True)  # Google Calendar event ID for sync
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class Deal(Base):
    """Sales opportunities and leads for follow-up calls"""
    __tablename__ = "deals"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    value = Column(Integer, nullable=True)  # Store as cents
    stage = Column(Text, nullable=False, default="lead")  # lead, qualified, proposal, negotiation, closed_won, closed_lost
    probability = Column(Integer, default=50)  # 0-100
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=True)
    assigned_to = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AppointmentReminder(Base):
    """Scheduled reminders for appointments"""
    __tablename__ = "appointment_reminders"
    
    id = Column(String(50), primary_key=True, index=True)
    appointment_id = Column(String(50), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    reminder_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Text, nullable=False, default="pending")  # pending, sent, failed
    communication_id = Column(String(50), ForeignKey("communications.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KnowledgeBaseSource(Base):
    __tablename__ = "knowledge_base_sources"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False) # 'website_crawler', 'file_upload', etc.
    name = Column(String(255), nullable=False)
    config = Column(JSON, nullable=True)
    status = Column(String(50), default="pending") # pending, syncing, active, error, paused
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    document_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Campaign(Base):
    """
    Marketing/Automation campaigns (e.g., Appointment Reminders, Lead Nurture)
    """
    __tablename__ = "campaigns"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Trigger Configuration
    trigger_type = Column(String(50), nullable=False)  # 'event' (appointment_booked), 'manual', 'segment'
    trigger_event = Column(String(50), nullable=True)  # 'appointment_booked', 'status_change', 'new_lead'
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active") # active, paused, cancelled, draft, completed
    stop_on_response = Column(Boolean, default=True) # Automatically stop campaign if customer replies
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    steps = relationship("CampaignStep", back_populates="campaign", order_by="CampaignStep.step_order", cascade="all, delete-orphan")


class CampaignStep(Base):
    """
    Individual steps in a campaign workflow
    """
    __tablename__ = "campaign_steps"
    
    id = Column(String(50), primary_key=True, index=True)
    campaign_id = Column(String(50), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)  # 1, 2, 3...
    
    type = Column(String(50), nullable=False)  # 'sms', 'email', 'call', 'wait'
    config = Column(JSON, nullable=True)       # { "template_body": "...", "delay_minutes": 60 }
    
    # Timing Logic
    delay_minutes = Column(Integer, default=0) # Delay before this step runs
    time_reference = Column(String(50), default="previous_step") # 'previous_step', 'trigger_time', 'appointment_date'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    campaign = relationship("Campaign", back_populates="steps")


class CampaignEnrollment(Base):
    """
    Tracks a customer's progress through a campaign
    """
    __tablename__ = "campaign_enrollments"
    
    id = Column(String(50), primary_key=True, index=True)
    campaign_id = Column(String(50), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Context
    reference_id = Column(String(50), nullable=True) # e.g., appointment_id or deal_id causing this enrollment
    
    # State
    current_step_order = Column(Integer, default=1)
    status = Column(String(50), default="active") # 'active', 'completed', 'cancelled', 'failed'
    
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True) # When the next step should execute
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# =====================================================
# WORKER MODELS (Autonomous Agents)
# =====================================================

class WorkerTemplate(Base):
    """
    Stores reusable worker type definitions with dynamic parameter schemas.
    Forms are auto-generated from parameter_schema (JSON Schema).
    """
    __tablename__ = "worker_templates"

    id = Column(String(50), primary_key=True, index=True)  # UUID
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")
    
    # Core configuration
    default_instructions = Column(Text, nullable=True)
    parameter_schema = Column(JSON, default={})  # JSON Schema for dynamic forms
    
    # Tool and integration requirements
    required_tools = Column(JSON, default=[])
    required_integrations = Column(JSON, default=[])

    # Outcome & Pricing Configuration
    outcome_price = Column(Integer, default=0) # Price per successful outcome in cents
    evaluation_logic = Column(JSON, default={}) # Logic for The Evaluator
    
    # UI/Display
    icon = Column(String(50), default="bot")
    color = Column(String(20), default="orange")
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkerTask(Base):
    """
    Stores individual task executions for workers.
    Tracks status, input/output, progress, and logs.
    """
    __tablename__ = "worker_tasks"

    id = Column(String(50), primary_key=True, index=True)  # UUID
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Task identification
    template_id = Column(String(50), ForeignKey("worker_templates.id"), nullable=True)
    worker_type = Column(String(100), nullable=False)
    
    # User/Customer context
    customer_id = Column(String(100), nullable=True)
    created_by_user_id = Column(String(50), nullable=True)
    
    # Status tracking: 'pending', 'running', 'completed', 'failed', 'cancelled'
    status = Column(String(20), default="pending", nullable=False)
    
    # Input/Output
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)

    # Outcome Verification
    outcome_status = Column(String(50), default="pending_eval") # pending_eval, success, failure, neutral
    outcome_score = Column(Float, nullable=True) # 0.0 to 1.0 confidence score
    
    # Progress tracking (for UI)
    steps_completed = Column(Integer, default=0)
    steps_total = Column(Integer, nullable=True)
    current_step = Column(String(255), nullable=True)
    
    # Execution logs
    logs = Column(JSON, default=[])
    error_message = Column(Text, nullable=True)
    
    # Analytics
    tokens_used = Column(Integer, default=0)
    api_calls = Column(JSON, default={})
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rating / Quality
    rating = Column(Integer, nullable=True)  # 1-5 stars
    rating_feedback = Column(Text, nullable=True)
    rated_at = Column(DateTime(timezone=True), nullable=True)
    rated_by_user_id = Column(String(50), nullable=True)
    
    # Billing
    base_fee_cents = Column(Integer, default=0)
    token_fee_cents = Column(Integer, default=0)
    outcome_fee_cents = Column(Integer, default=0)
    total_fee_cents = Column(Integer, default=0)
    fee_billed = Column(Boolean, default=False)
    
    # Agent Attribution
    dispatched_by_agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)


class WorkerSchedule(Base):
    """
    Defines a recurring schedule for a worker task.
    """
    __tablename__ = "worker_schedules"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    worker_type = Column(String(100), nullable=False)
    
    # Scheduling definition
    schedule_expression = Column(String(100), nullable=False)  # e.g. "daily at 9am" or cron "0 9 * * *"
    cron_expression = Column(String(100), nullable=True)       # Parsed cron format for technical execution
    timezone = Column(String(50), default="UTC")
    
    # Task Configuration
    input_data = Column(JSON, default={})
    
    # State
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by_user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkerInstance(Base):
    """
    Represents a provisioned infrastructure instance (e.g. Docker container) for an AI Worker.
    Supports scaling (multiple instances) and tiered specs.
    """
    __tablename__ = "worker_instances"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Identification
    name = Column(String(100), nullable=False) # e.g. "Clawdbot-01", "Scraper Cluster"
    worker_type = Column(String(100), nullable=False) # e.g. "clawdbot"
    
    # Infrastructure Specs
    tier = Column(String(50), default="standard") # 'standard', 'performance'
    files_disk_size_gb = Column(Integer, default=10)
    
    # State
    # State
    status = Column(String(50), default="provisioning") # provisioning, active, offline, error, terminated
    
    # BYO / Connection Info
    is_external = Column(Boolean, default=False)
    connection_url = Column(String(255), nullable=True) # e.g. https://my-claw.railway.app
    api_key_ref = Column(String(255), nullable=True) # Reference to KeyVault or Encrypted Key
    
    # Legacy / Internal (Keeping for compatibility or internal tiers)
    container_id = Column(String(255), nullable=True) 
    ip_address = Column(String(50), nullable=True)
    
    # Cost Tracking
    monthly_cost_cents = Column(Integer, default=0) # Stored in cents
    billing_start_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by_user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    instructions = Column(Text, nullable=False)
    parameter_schema = Column(JSONB, nullable=True)
    allowed_tools = Column(ARRAY(String), nullable=True) # List of tool names
    is_system = Column(Boolean, default=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentSkill(Base):
    __tablename__ = "agent_skills"

    id = Column(String(50), primary_key=True, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String(50), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB, nullable=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)

class AgentPersonality(Base):
    __tablename__ = "agent_personalities"

    id = Column(String(50), primary_key=True, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False)
    communication_style = Column(String(50), nullable=True)
    core_values = Column(Text, nullable=True)
    tone_guide = Column(Text, nullable=True)
    good_examples = Column(Text, nullable=True)
    bad_examples = Column(Text, nullable=True)
    brand_voice = Column(JSONB, nullable=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)

class WorkspaceLLMConfig(Base):
    __tablename__ = "workspace_llm_config"

    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider = Column(String(20), default="openai")
    model = Column(String(50), default="gpt-4o")
    api_key_encrypted = Column(Text, nullable=True)
    is_byok = Column(Boolean, default=False)
    monthly_token_usage = Column(Integer, default=0)
    rate_limit_rpm = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MCPServer(Base):
    """Workspace-level MCP (Model Context Protocol) server connections"""
    __tablename__ = "mcp_servers"
    
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    transport = Column(String(20), default="sse")       # "sse" | "stdio"
    auth_type = Column(String(20), default="none")      # "api_key" | "bearer" | "none"
    auth_value = Column(Text, nullable=True)
    status = Column(String(20), default="pending")      # "connected" | "error" | "pending"
    tools_cache = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    workspace = relationship("Workspace")
