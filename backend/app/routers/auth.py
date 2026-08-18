from fastapi import APIRouter, Depends, HTTPException, status
router = APIRouter()
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt as _bcrypt
import hashlib
import binascii

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.invitation import Invitation
from app.models.business import Business
from app.core.config import settings
import logging

from fastapi import Request, Response
from authlib.integrations.starlette_client import OAuth
from app.auth.utils import get_or_create_user_by_email, pwd_context, hash_password
from app.core.dependencies import get_current_user
import uuid
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# In-memory store for OAuth codes (FYP-level approach)
OAUTH_CODES = {}

# Initialize OAuth client
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get('/google')
async def google_login(request: Request, invite_token: str | None = None):
    """Redirect user to Google consent screen"""
    # Keep the invitation in the signed session across the OAuth round trip.
    # The token is not included in the parameters sent to Google.
    if invite_token:
        request.session['google_invite_token'] = invite_token
    else:
        request.session.pop('google_invite_token', None)
    return await oauth.google.authorize_redirect(
        request, settings.GOOGLE_OAUTH_REDIRECT_URI
    )


def _accept_google_invitation(
    db: Session,
    invite_token: str,
    email: str,
    name: str,
    google_id: str | None,
    avatar_url: str | None,
) -> User:
    """Create the invited user in the invitation's tenant using Google identity."""
    invitation = (
        db.query(Invitation)
        .filter(Invitation.token == invite_token)
        .with_for_update()
        .first()
    )
    if not invitation or invitation.revoked or invitation.accepted:
        raise ValueError('invalid_invitation')

    now = datetime.now(timezone.utc) if invitation.expires_at.tzinfo else datetime.utcnow()
    if invitation.expires_at < now:
        raise ValueError('expired_invitation')
    if email.strip().lower() != invitation.email.strip().lower():
        raise ValueError('invite_email_mismatch')
    if not db.query(Business).filter(Business.id == invitation.business_id).first():
        raise ValueError('invalid_invitation')
    if db.query(User).filter(User.email == email.strip().lower()).first():
        raise ValueError('email_already_registered')

    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        hashed_password=hash_password(str(uuid.uuid4())),
        role=invitation.role,
        business_id=invitation.business_id,
        provider='google',
        email_verified=True,
        google_id=google_id,
        avatar_url=avatar_url,
        status='offline',
    )
    db.add(user)
    invitation.accepted = True
    db.commit()
    db.refresh(user)
    return user


def _oauth_error_response(error: str, invite_token: str | None = None) -> Response:
    if invite_token:
        query = urlencode({'token': invite_token, 'oauth_error': error})
        location = f"{settings.FRONTEND_URL}/accept-invite?{query}"
    else:
        location = f"{settings.FRONTEND_URL}/oauth/callback?error={error}"
    return Response(status_code=302, headers={'Location': location})

@router.get('/google/callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback, exchange code, issue JWT and redirect to frontend"""
    stage = "token_exchange"
    invite_token = request.session.pop('google_invite_token', None)
    try:
        token = await oauth.google.authorize_access_token(request)

        # Try userinfo endpoint first, fall back to id_token claims
        stage = "userinfo"
        userinfo = token.get('userinfo')
        if not userinfo:
            userinfo = await oauth.google.userinfo(token=token)

        email = userinfo.get('email')
        if email:
            email = email.strip().lower()
        name = userinfo.get('name') or (email.split('@')[0] if email else '')
        email_verified = userinfo.get('email_verified', False)
        google_id = userinfo.get('sub')
        avatar_url = userinfo.get('picture')
        if not email:
            raise ValueError('Email not provided by Google')
        if not email_verified:
            return _oauth_error_response('unverified_email', invite_token)
        # Invitation sign-up must use the invited email and tenant. Ordinary
        # Google sign-in keeps the existing get-or-create behaviour.
        stage = "user_and_business_link"
        if invite_token:
            user = _accept_google_invitation(
                db, invite_token, email, name, google_id, avatar_url
            )
        else:
            user = get_or_create_user_by_email(db, email, name, google_id=google_id, avatar_url=avatar_url)
        # Create temporary one-time code storing user ID
        code = str(uuid.uuid4())
        OAUTH_CODES[code] = user.id

        # Build redirect URL for frontend callback using the code only
        redirect_url = f"{settings.FRONTEND_URL}/oauth/callback?code={code}"
        return Response(status_code=302, headers={'Location': redirect_url})
    except ValueError as e:
        db.rollback()
        return _oauth_error_response(str(e), invite_token)
    except Exception as e:
        db.rollback()
        logger.exception(
            "Google OAuth callback failed at stage=%s error_type=%s",
            stage,
            type(e).__name__,
        )
        return _oauth_error_response('oauth_failed', invite_token)

def _check_password(plain_password: str, hashed_password: str) -> bool:
    """Try bcrypt directly first, then fall back to legacy PBKDF2."""
    # Try bcrypt directly (avoids passlib/bcrypt version incompatibility)
    try:
        if _bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
    except Exception as e:
        logging.warning(f"[_check_password] bcrypt.checkpw error: {e}")
    # Fallback to legacy PBKDF2
    try:
        salt = hashed_password[:64].encode('ascii')
        stored_hash = hashed_password[64:].encode('ascii')
        new_hash = hashlib.pbkdf2_hmac(
            'sha512', plain_password.encode('utf-8'), salt, 100000
        )
        new_hash = binascii.hexlify(new_hash)
        return new_hash == stored_hash
    except Exception as e:
        logging.warning(f"[_check_password] PBKDF2 error: {e}")
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

from pydantic import BaseModel

class OAuthExchangeRequest(BaseModel):
    code: str

@router.post('/oauth/exchange')
async def oauth_exchange(request: OAuthExchangeRequest, db: Session = Depends(get_db)):
    code = request.code
    if code not in OAUTH_CODES:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth code")
    
    user_id = OAUTH_CODES.pop(code)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)

    access_token = create_access_token(
        data={"sub": user.email, "role": role_str, "name": user.name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role_str,
            "business_id": user.business_id
        }
    }

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username.strip().lower()).first()
    
    # Check email and password
    if not user or not _check_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    access_token = create_access_token(
        data={"sub": user.email, "role": role_str, "name": user.name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role_str,
            "business_id": user.business_id
        }
    }

@router.get('/me')
async def read_current_user(current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": role_str,
        "status": current_user.status,
        "business_id": current_user.business_id,
        "provider": current_user.provider,
        "avatar_url": current_user.avatar_url,
        "email_verified": current_user.email_verified,
    }


@router.post('/presence')
async def update_presence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Heartbeat used by the authenticated app shell."""
    current_user.status = "online"
    current_user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "online", "last_seen_at": current_user.last_seen_at}


@router.post('/logout')
async def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.status = "offline"
    current_user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "offline"}

@router.post('/register')
async def register_user(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    name = (payload.get('name') or payload.get('fullName') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password')
    business_name = (payload.get('business_name') or payload.get('businessName') or '').strip()

    if not name:
        raise HTTPException(status_code=400, detail='Full name is required')
    if not business_name:
        raise HTTPException(status_code=400, detail='Business name is required')
    if not email or not password:
        raise HTTPException(status_code=400, detail='Missing required fields')

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')

    business_id = None
    if business_name:
        from app.models.business import Business
        # SECURITY FIX: always create NEW business, never attach to existing
        # This prevents tenant takeover via registration
        existing_business = db.query(Business).filter(
            Business.name == business_name
        ).first()
        if existing_business:
            raise HTTPException(
                status_code=400,
                detail='A business with this name already exists. Contact the business admin for an invitation.'
            )
        new_business = Business(name=business_name)
        db.add(new_business)
        db.commit()
        db.refresh(new_business)
        business_id = new_business.id

    hashed_password = hash_password(password)
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=UserRole.BUSINESS_ADMIN,
        provider='local',
        email_verified=True,
        business_id=business_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "business_id": new_user.business_id
    }


from app.services.email_service import send_password_reset_email
from pydantic import BaseModel, EmailStr
import time


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Always return success even if email doesn't exist (prevents email enumeration)
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    reset_payload = {
        "sub": user.email,
        "type": "password_reset",
        "exp": int(time.time()) + 3600  # 1 hour
    }
    reset_token = jwt.encode(reset_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    send_password_reset_email(
        to_email=user.email,
        reset_url=reset_url,
        user_name=user.name
    )

    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        email = decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Reset link expired or invalid")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = pwd_context.hash(payload.new_password)
    db.commit()

    return {"message": "Password reset successful. You can now login with your new password."}
