from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.business import Business
from app.core.dependencies import get_current_user, require_business_admin

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
        "onboarding_completed": business.onboarding_completed is True,
    }

@router.patch("/business")
async def update_business_settings(
    payload: BusinessUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    if not current_user.business_id:
        raise HTTPException(status_code=403, detail="No business associated")

    business = db.query(Business).filter(
        Business.id == current_user.business_id
    ).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if payload.name is not None:
        normalized_name = payload.name.strip()
        duplicate = db.query(Business).filter(Business.name == normalized_name, Business.id != business.id).first() if normalized_name else None
        if duplicate:
            raise HTTPException(status_code=400, detail="A business with this name already exists.")
        business.name = normalized_name
    if payload.email is not None:
        business.email = payload.email
    if payload.phone is not None:
        business.phone = payload.phone
    if payload.website is not None:
        business.website = payload.website
    if payload.description is not None:
        business.description = payload.description
    # Completing the profile is the only way to clear the first-login gate for
    # a Google-created business admin. Invited teammates never reach this
    # admin-only endpoint and are therefore unaffected.
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role == "business_admin" and (current_user.provider or "").lower() == "google" and business.onboarding_completed is not True:
        required = {
            "Business name": business.name,
            "Business email": business.email,
            "Website": business.website,
            "Phone": business.phone,
        }
        missing = [label for label, value in required.items() if not value or not str(value).strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"Please complete: {', '.join(missing)}")
        business.onboarding_completed = True
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
        "onboarding_completed": business.onboarding_completed is True,
    }}
