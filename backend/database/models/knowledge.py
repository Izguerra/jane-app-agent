from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, JSON, func
from backend.database import Base

class KnowledgeBaseSource(Base):
    __tablename__ = "knowledge_base_sources"
    id = Column(String(50), primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    config = Column(JSON)
    status = Column(String(50), default="pending")
    last_synced_at = Column(DateTime(timezone=True))
    document_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    content_hash = Column(String(64))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
