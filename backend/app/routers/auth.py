from fastapi import APIRouter, Depends, HTTPException, status
router = APIRouter()
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt as _bcrypt
import hashlib
import binascii
import traceback

from app.core.database import get_db
from app.models.user import User, UserRole
from app.core.config import settings
import logging

from fastapi import Request, Response
from authlib.integrations.starlette_client import OAuth
from app.auth.utils import get_or_create_user_by_email, pwd_context, hash_password

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
async def google_login(request: Request):
    """Redirect user to Google consent screen"""
    redirect_uri = 'http://localhost:8000/api/v1/auth/google/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/google/callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback, exchange code, issue JWT and redirect to frontend"""
    try:
        token = await oauth.google.authorize_access_token(request)

        # Try userinfo endpoint first, fall back to id_token claims
        userinfo = token.get('userinfo')
        if not userinfo:
            userinfo = await oauth.google.userinfo(token=token)

        email = userinfo.get('email')
        name = userinfo.get('name') or (email.split('@')[0] if email else '')
        email_verified = userinfo.get('email_verified', False)
        google_id = userinfo.get('sub')
        avatar_url = userinfo.get('picture')
        if not email:
            raise ValueError('Email not provided by Google')
        if not email_verified:
            error_url = f"{settings.FRONTEND_URL}/oauth/callback?error=unverified_email"
            return Response(status_code=302, headers={'Location': error_url})
        # Get or create local user, passing google fields
        user = get_or_create_user_by_email(db, email, name, google_id=google_id, avatar_url=avatar_url)
        # Create JWT
        jwt_token = create_access_token({
            'sub': user.email,
            'role': user.role,
            'name': user.name,
        })
        # Build redirect URL for frontend callback
        redirect_url = (
            f"{settings.FRONTEND_URL}/oauth/callback?"
            f"token={jwt_token}&name={user.name}&email={user.email}&role={user.role}"
        )
        if user.business_id:
            redirect_url += f"&business_id={user.business_id}"
        return Response(status_code=302, headers={'Location': redirect_url})
    except Exception as e:
        logging.error("OAuth callback error full traceback:")
        logging.error(traceback.format_exc())
        error_url = f"{settings.FRONTEND_URL}/oauth/callback?error=oauth_failed"
        return Response(status_code=302, headers={'Location': error_url})

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

# Dependency to retrieve current user from JWT
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing or invalid token')
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get('sub')
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token decode error')
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check email and password
    if not user or not _check_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "business_id": user.business_id
        }
    }

@router.get('/me')
async def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
        "business_id": current_user.business_id,
        "provider": current_user.provider,
        "avatar_url": current_user.avatar_url,
        "email_verified": current_user.email_verified,
    }

@router.post('/register')
async def register_user(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    name = payload.get('name') or payload.get('fullName')
    email = payload.get('email')
    password = payload.get('password')
    business_name = payload.get('business_name') or payload.get('businessName')

    if not all([name, email, password]):
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
