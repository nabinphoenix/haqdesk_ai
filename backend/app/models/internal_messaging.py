from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.sql import func

from ..core.database import Base


class InternalThread(Base):
    __tablename__ = "internal_threads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class InternalThreadParticipant(Base):
    __tablename__ = "internal_thread_participants"
    __table_args__ = (UniqueConstraint("thread_id", "user_id", name="uq_internal_thread_user"),)

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("internal_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InternalMessage(Base):
    __tablename__ = "internal_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("internal_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
