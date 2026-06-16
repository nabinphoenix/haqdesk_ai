from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class IntegrationCreate(BaseModel):
    business_id: int
    platform: str

class IntegrationResponse(BaseModel):
    id: int
    business_id: int
    platform: str
    status: str
    created_at: datetime
    metadata_json: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class OAuthCallbackData(BaseModel):
    code: str
    state: str

class PlatformMessagePayload(BaseModel):
    """Generic schema for normalized platform messages"""
    platform: str
    sender_id: str
    sender_name: Optional[str] = None
    message_text: str
    timestamp: datetime
    conversation_id: Optional[str] = None
    metadata: Optional[Dict] = None
