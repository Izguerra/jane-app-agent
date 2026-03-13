from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime, JSON, func
from sqlalchemy.orm import relationship
from backend.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String(50), primary_key=True, index=True)
    team_id = Column(String(50), ForeignKey("teams.id"), nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    description = Column(Text)
    services = Column(Text)
    business_hours = Column(Text)
    faq = Column(Text)
    reference_urls = Column(Text)
    conversations_this_month = Column(Integer, default=0)
    voice_minutes_this_month = Column(Integer, default=0)
    inbound_agent_phone = Column(String(50), unique=True)
    churn_threshold_days = Column(Integer, default=90)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MCPServer(Base):
    __tablename__ = "mcp_servers"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    transport = Column(String(20), default="sse")
    auth_type = Column(String(20), default="none")
    auth_value = Column(Text)
    status = Column(String(20), default="pending")
    tools_cache = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    workspace = relationship("Workspace")

class PlatformIntegration(Base):
    __tablename__ = "platform_integrations"
    id = Column(String(50), primary_key=True, index=True)
    provider = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), nullable=False)
    credentials = Column(Text)  # Encrypted JSON
    settings = Column(Text)     # Plain JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class WorkspaceLLMConfig(Base):
    __tablename__ = "workspace_llm_configs"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), nullable=False, default="openai")
    model = Column(String(100), nullable=False, default="gpt-4o")
    is_byok = Column(Boolean, default=False)
    api_key_encrypted = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
