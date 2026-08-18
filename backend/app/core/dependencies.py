from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to retrieve current user from Authorization Bearer JWT"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Missing or invalid token. Ensure Authorization: Bearer <token> is set.'
        )
    
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


def require_business_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require an administrator role for business-wide mutations."""
    if current_user.role not in ("business_admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    if current_user.role != "super_admin" and not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No business associated",
        )
    return current_user


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super administrator access required",
        )
    return current_user


def require_business_analytics(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow tenant-wide analytics only to business admins and supervisors."""
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business analytics require an authenticated business context",
        )
    if current_user.role not in ("business_admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business analytics access requires an admin or supervisor role",
        )
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No business associated with this account",
        )
    return current_user
