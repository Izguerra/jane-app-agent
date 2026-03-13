from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime, JSON, func
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.database.models.utils import JSONB, ARRAY

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False, default="My Agent")
    voice_id = Column(String(50))
    language = Column(String(10), default="en")
    prompt_template = Column(Text)
    welcome_message = Column(Text)
    soul = Column(Text)
    is_orchestrator = Column(Boolean, default=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON)
    allowed_worker_types = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    phone_numbers = relationship("PhoneNumber", back_populates="agent")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    instructions = Column(Text, nullable=False)
    parameter_schema = Column(JSONB)
    allowed_tools = Column(ARRAY(String))
    is_system = Column(Boolean, default=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentSkill(Base):
    __tablename__ = "agent_skills"
    id = Column(String(50), primary_key=True, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String(50), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)

class AgentPersonality(Base):
    __tablename__ = "agent_personalities"
    id = Column(String(50), primary_key=True, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False)
    communication_style = Column(String(50))
    core_values = Column(Text)
    tone_guide = Column(Text)
    good_examples = Column(Text)
    bad_examples = Column(Text)
    brand_voice = Column(JSONB)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
