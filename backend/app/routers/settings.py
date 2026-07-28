from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.business import Business
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

class BusinessUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    ai_response_mode: Optional[str] = None

@router.get("/business")
async def get_business_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.business_id:
        raise HTTPException(status_code=404, detail="No business associated")

    business = db.query(Business).filter(
        Business.id == current_user.business_id
    ).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return {
        "id": business.id,
        "name": business.name,
        "email": business.email,
        "phone": business.phone,
        "website": business.website,
        "description": business.description,
        "is_active": business.is_active,
        "ai_response_mode": business.ai_response_mode or "review",
    }

@router.patch("/business")
async def update_business_settings(
    payload: BusinessUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.business_id:
        raise HTTPException(status_code=403, detail="No business associated")

    business = db.query(Business).filter(
        Business.id == current_user.business_id
    ).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if payload.name is not None:
        business.name = payload.name
    if payload.email is not None:
        business.email = payload.email
    if payload.phone is not None:
        business.phone = payload.phone
    if payload.website is not None:
        business.website = payload.website
    if payload.description is not None:
        business.description = payload.description
    if payload.ai_response_mode is not None:
        if payload.ai_response_mode not in ["review", "auto"]:
            raise HTTPException(status_code=400, detail="Invalid ai_response_mode. Must be 'review' or 'auto'")
        business.ai_response_mode = payload.ai_response_mode

    db.commit()
    db.refresh(business)

    return {"message": "Business settings updated", "business": {
        "name": business.name,
        "email": business.email,
        "phone": business.phone,
        "website": business.website,
        "description": business.description,
        "ai_response_mode": business.ai_response_mode,
    }}
