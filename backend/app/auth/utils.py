from uuid import uuid4
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import bcrypt
from app.models.user import User, UserRole
from app.models.business import Business

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception:
        return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False


def get_or_create_user_by_email(
    db: Session,
    email: str,
    name: str,
    google_id: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Retrieve a user by email or create a new Google-authenticated user.

    For Google sign‑in we generate a random password hash (unused) and set:
    * role = UserRole.BUSINESS_ADMIN
    * provider = "google"
    * email_verified = True
    * optional google_id and avatar_url
    """
    normalized_email = email.strip().lower()
    # Try to find existing user
    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        # Update Google fields if they were not set previously
        if google_id and not user.google_id:
            user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user

    # A Google sign-up has no business-name field. Create a tenant for the new
    # business admin instead of leaving them on the invalid business_id=NULL path.
    display_name = name.strip() if name and name.strip() else normalized_email.split('@')[0]
    base_business_name = f"{display_name}'s Business"
    business_name = base_business_name
    suffix = 2
    while db.query(Business).filter(Business.name == business_name).first():
        business_name = f"{base_business_name} {suffix}"
        suffix += 1

    # A brand-new Google business starts in onboarding until its admin confirms the profile.
    business = Business(name=business_name, email=normalized_email, onboarding_completed=False)
    db.add(business)
    db.flush()

    # Create a new user with a random unusable password
    random_password = str(uuid4())
    hashed_password = hash_password(random_password)
    role_value = UserRole.BUSINESS_ADMIN.value if hasattr(UserRole.BUSINESS_ADMIN, 'value') else "business_admin"
    new_user = User(
        name=display_name,
        email=normalized_email,
        hashed_password=hashed_password,
        role=role_value,
        provider="google",
        email_verified=True,
        google_id=google_id,
        avatar_url=avatar_url,
        business_id=business.id,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise
    return new_user
