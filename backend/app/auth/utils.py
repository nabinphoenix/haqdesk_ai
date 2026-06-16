from uuid import uuid4
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import bcrypt
from app.models.user import User, UserRole

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
    # Try to find existing user
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Update Google fields if they were not set previously
        if google_id and not user.google_id:
            user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user

    # Create a new user with a random unusable password
    random_password = str(uuid4())
    hashed_password = hash_password(random_password)
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=UserRole.BUSINESS_ADMIN,
        provider="google",
        email_verified=True,
        google_id=google_id,
        avatar_url=avatar_url,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
