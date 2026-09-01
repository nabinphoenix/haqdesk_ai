from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class FAQOpportunityFeedback(Base):
    """Tenant-scoped review state for dynamically discovered FAQ opportunities."""

    __tablename__ = "faq_opportunity_feedback"
    __table_args__ = (
        UniqueConstraint("business_id", "fingerprint", name="uq_faq_opportunity_business_fingerprint"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active")
    knowledge_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)