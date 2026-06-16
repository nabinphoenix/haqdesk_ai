from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from ..core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_type = Column(String) # customer, agent, AI
    sender_id = Column(Integer, nullable=True) # User ID if sender_type is agent
    content = Column(Text)
    message_type = Column(String, default="text") # text, image, file
    platform = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ai_draft = Column(Text, nullable=True)
    ai_language = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
