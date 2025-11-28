from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func

# Handle both import contexts (uvicorn vs direct execution)
try:
    from backend.database import Base
except ModuleNotFoundError:
    from database import Base

class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, nullable=False) # Maps to Next.js teams.id
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    description = Column(Text)
    business_hours = Column(Text) # JSON string: {"monday": {"open": "9:00", "close": "17:00"}, ...}
    services = Column(Text)
    faq = Column(Text) # JSON string: [{"question": "...", "answer": "..."}, ...]
    reference_urls = Column(Text) # JSON string: ["url1", "url2", ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AgentSettings(Base):
    __tablename__ = "agent_settings"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    voice_id = Column(String(50))
    language = Column(String(10), default="en")
    prompt_template = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CommunicationLog(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    type = Column(String(20), nullable=False) # 'call' or 'chat'
    direction = Column(String(20), nullable=False) # 'inbound' or 'outbound'
    status = Column(String(20), nullable=False) # 'completed', 'missed', 'failed'
    duration = Column(Integer, default=0)
    transcript = Column(Text)
    summary = Column(Text)
    sentiment = Column(String(20)) # 'positive', 'neutral', 'negative'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(Text) # Extracted text content
    file_type = Column(String(50)) # 'pdf', 'txt', 'url'
    file_path = Column(String(500)) # Path to stored file or URL
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

