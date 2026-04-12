from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from backend.database import Base

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"))
    customer_first_name = Column(String(100))
    customer_last_name = Column(String(100))
    customer_email = Column(String(255))
    customer_phone = Column(String(50))
    title = Column(Text, nullable=False)
    description = Column(Text)
    appointment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    status = Column(Text, nullable=False, default="scheduled")
    location = Column(Text)
    notes = Column(Text)
    calendar_event_id = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AppointmentReminder(Base):
    __tablename__ = "appointment_reminders"
    id = Column(String(50), primary_key=True, index=True)
    appointment_id = Column(String(50), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    reminder_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Text, nullable=False, default="pending")
    communication_id = Column(String(50), ForeignKey("communications.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String(50), unique=True, nullable=False, index=True)
    friendly_name = Column(String(255))
    country_code = Column(String(2))
    voice_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    voice_url = Column(Text)
    whatsapp_webhook_url = Column(Text)
    twilio_sid = Column(String(255), unique=True, index=True)
    telnyx_id = Column(String(255), unique=True, index=True)
    provider = Column(String(50), default="twilio", nullable=False)
    agent_id = Column(String(50), ForeignKey("agents.id", ondelete="SET NULL"))
    stripe_subscription_item_id = Column(String(255))
    monthly_cost = Column(Integer)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    workspace = relationship("Workspace")
    agent = relationship("Agent", back_populates="phone_numbers")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(10), default="en")
    category = Column(String(50))
    status = Column(String(50))
    template_id = Column(String(255))
    components = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
