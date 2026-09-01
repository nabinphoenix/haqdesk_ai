from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)
    source_type = Column(String, default='upload', nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    checksum = Column(String(64), nullable=True, index=True)
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    ingestion_attempts = Column(Integer, default=0, nullable=False)
    status = Column(String, default="processing")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete")


class KnowledgeIngestionJob(Base):
    __tablename__ = 'knowledge_ingestion_jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String, default='pending', nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    available_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    document = relationship('KnowledgeDocument')


class AgentReplyFeedback(Base):
    __tablename__ = 'agent_reply_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    question = Column(Text, nullable=False)
    ai_draft = Column(Text, nullable=True)
    approved_answer = Column(Text, nullable=False)
    indexed = Column(Boolean, default=False, nullable=False)
    knowledge_document_id = Column(Integer, ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    document = relationship("KnowledgeDocument", back_populates="chunks")
