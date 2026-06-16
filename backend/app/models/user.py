from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from ..core.database import Base
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    BUSINESS_ADMIN = "business_admin"
    AGENT = "agent"
    SUPERVISOR = "supervisor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.BUSINESS_ADMIN)
    status = Column(String, default="offline")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # OAuth and verification fields
    provider = Column(String, default="local")
    google_id = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
