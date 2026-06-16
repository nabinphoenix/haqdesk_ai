from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from ..core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    platform = Column(String) # facebook, whatsapp, instagram
    platform_user_id = Column(String, index=True)
    display_name = Column(String)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    is_merged = Column(Boolean, default=False)
    merged_into_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    potential_match_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
