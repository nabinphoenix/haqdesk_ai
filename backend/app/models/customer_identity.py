from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class CustomerIdentity(Base):
    __tablename__ = "customer_identities"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    master_customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    linked_customer_id = Column(Integer, ForeignKey("customers.id"), unique=True)
    linked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
