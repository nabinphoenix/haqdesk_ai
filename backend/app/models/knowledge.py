from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, default="processing")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    document = relationship("KnowledgeDocument", back_populates="chunks")