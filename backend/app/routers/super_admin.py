import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.auth.utils import hash_password
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.models.faq_opportunity import FAQOpportunityFeedback
from app.models.integration import Integration
from app.models.internal_messaging import InternalMessage, InternalThread, InternalThreadParticipant
from app.models.invitation import Invitation
from app.models.knowledge import AgentReplyFeedback, KnowledgeChunk, KnowledgeDocument, KnowledgeIngestionJob
from app.models.message import Message
from app.models.user import User, UserRole
from app.services.rag_service import rag_service


router = APIRouter(prefix="/super-admin", tags=["super-admin"])


def _iso(value):
    return value.isoformat() if value else None


def _business_json(business: Business, owner: User | None = None) -> dict:
    return {
        'id': business.id,
        'name': business.name,
        'email': business.email,
        'phone': business.phone,
        'website': business.website,
        'description': business.description,
        'is_active': bool(business.is_active),
        'onboarding_completed': business.onboarding_completed is True,
        'created_at': _iso(business.created_at),
        'updated_at': _iso(business.updated_at),
        'owner': {
            'id': owner.id,
            'name': owner.name,
            'email': owner.email,
        } if owner else None,
    }


def _owner_for_business(db: Session, business_id: int) -> User | None:
    return db.query(User).filter(
        User.business_id == business_id,
        User.role == UserRole.BUSINESS_ADMIN.value,
    ).order_by(User.created_at.asc()).first()


def _mail_config() -> ConnectionConfig | None:
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        return None
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM or settings.MAIL_USERNAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


def _invite_url(invitation: Invitation) -> str:
    return settings.FRONTEND_URL.rstrip('/') + '/accept-invite?token=' + invitation.token


def _user_json(user: User, business_name: str | None = None) -> dict:
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'business_id': user.business_id,
        'business_name': business_name,
        'provider': user.provider,
        'created_at': _iso(user.created_at),
    }


class BusinessCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    is_active: bool = True
    owner_email: EmailStr | None = None
    send_owner_invitation: bool = True


class BusinessUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    is_active: bool | None = None
    onboarding_completed: bool | None = None


class OwnerInvitationRequest(BaseModel):
    email: EmailStr


class TeamInvitationRequest(BaseModel):
    email: EmailStr
    role: str = Field(default='agent')


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    business_id: int = Field(gt=0)
    role: str = Field(default='agent')


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    business_id: int | None = Field(default=None, gt=0)
    role: str | None = None
    status: str | None = Field(default=None, max_length=32)


class DeleteUserRequest(BaseModel):
    confirm_email: EmailStr


class DeleteBusinessRequest(BaseModel):
    confirm_name: str = Field(min_length=2, max_length=160)


MANAGED_ROLES = {
    UserRole.BUSINESS_ADMIN.value,
    UserRole.SUPERVISOR.value,
    UserRole.AGENT.value,
}


def _create_owner_invitation(db: Session, business: Business, email: str) -> Invitation:
    return _create_team_invitation(db, business, email, UserRole.BUSINESS_ADMIN.value)


def _create_team_invitation(db: Session, business: Business, email: str, role: str) -> Invitation:
    role = role.strip().lower()
    if role not in MANAGED_ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Choose business_admin, supervisor, or agent.')
    normalized_email = email.strip().lower()
    if db.query(User.id).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A HaqDesk user already exists with this email.')
    existing = db.query(Invitation).filter(
        Invitation.business_id == business.id,
        Invitation.email == normalized_email,
        Invitation.role == role,
        Invitation.accepted.is_(False),
        Invitation.revoked.is_(False),
        Invitation.expires_at > datetime.now(timezone.utc),
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='An active invitation already exists for this email and role.')
    invitation = Invitation(
        business_id=business.id,
        email=normalized_email,
        role=role,
        token=str(uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    return invitation


async def _send_invitation_email(email: str, business_name: str, role: str, invite_url: str) -> bool:
    configuration = _mail_config()
    if not configuration:
        return False
    role_label = role.replace('_', ' ')
    body = 'You are invited as a ' + role_label + ' for ' + business_name + ' on HaqDesk AI. Complete registration here: ' + invite_url
    message = MessageSchema(
        subject='Join ' + business_name + ' on HaqDesk AI',
        recipients=[email],
        body=body,
        subtype=MessageType.plain,
    )
    await FastMail(configuration).send_message(message)
    return True


@router.post('/businesses', status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    business_name = payload.name.strip()
    if db.query(Business.id).filter(func.lower(Business.name) == business_name.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A business with this name already exists.')

    business = Business(
        name=business_name,
        email=str(payload.email).lower() if payload.email else None,
        phone=(payload.phone or '').strip() or None,
        website=(payload.website or '').strip() or None,
        description=(payload.description or '').strip() or None,
        is_active=payload.is_active,
        # Super Admin created the tenant and its profile directly. The owner
        # invitation must not trigger the Google-only business onboarding form.
        onboarding_completed=True,
    )
    db.add(business)
    db.flush()

    invitation = None
    if payload.owner_email:
        invitation = _create_owner_invitation(db, business, str(payload.owner_email))
    db.commit()
    db.refresh(business)

    invitation_data = None
    if invitation:
        invite_url = _invite_url(invitation)
        mail_configured = _mail_config() is not None
        if payload.send_owner_invitation and mail_configured:
            background_tasks.add_task(
                _send_invitation_email,
                invitation.email,
                business.name,
                invitation.role,
                invite_url,
            )
        invitation_data = {
            'id': invitation.id,
            'email': invitation.email,
            'invite_url': invite_url,
            'email_queued': bool(payload.send_owner_invitation and mail_configured),
            'expires_at': _iso(invitation.expires_at),
        }
    return {'business': _business_json(business), 'owner_invitation': invitation_data}


@router.post('/businesses/{business_id}/owner-invitations', status_code=status.HTTP_201_CREATED)
def invite_business_owner(
    business_id: int,
    payload: OwnerInvitationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found.')
    invitation = _create_owner_invitation(db, business, str(payload.email))
    db.commit()
    invite_url = _invite_url(invitation)
    mail_configured = _mail_config() is not None
    if mail_configured:
        background_tasks.add_task(_send_invitation_email, invitation.email, business.name, invitation.role, invite_url)
    return {
        'id': invitation.id,
        'email': invitation.email,
        'role': invitation.role,
        'invite_url': invite_url,
        'email_queued': mail_configured,
        'expires_at': _iso(invitation.expires_at),
    }


@router.patch('/businesses/{business_id}')
def update_business(
    business_id: int,
    payload: BusinessUpdateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found.')
    updates = payload.model_dump(exclude_unset=True)
    if 'name' in updates:
        proposed = updates['name'].strip()
        duplicate = db.query(Business.id).filter(
            func.lower(Business.name) == proposed.lower(),
            Business.id != business_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A business with this name already exists.')
        business.name = proposed
    for field in ('email', 'phone', 'website', 'description', 'is_active', 'onboarding_completed'):
        if field in updates:
            value = updates[field]
            setattr(business, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(business)
    return {'business': _business_json(business, _owner_for_business(db, business.id))}


@router.post('/businesses/{business_id}/invitations', status_code=status.HTTP_201_CREATED)
def invite_business_team_member(
    business_id: int,
    payload: TeamInvitationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found.')
    invitation = _create_team_invitation(db, business, str(payload.email), payload.role)
    db.commit()
    invite_url = _invite_url(invitation)
    mail_configured = _mail_config() is not None
    if mail_configured:
        background_tasks.add_task(_send_invitation_email, invitation.email, business.name, invitation.role, invite_url)
    return {
        'id': invitation.id,
        'email': invitation.email,
        'role': invitation.role,
        'invite_url': invite_url,
        'email_queued': mail_configured,
        'expires_at': _iso(invitation.expires_at),
    }


@router.delete('/businesses/{business_id}')
def delete_business(
    business_id: int,
    payload: DeleteBusinessRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    '''Permanently delete one confirmed tenant and only its owned data.'''
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found.')
    if payload.confirm_name.strip() != business.name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Business name confirmation does not match.')

    storage_root = Path(settings.KNOWLEDGE_UPLOAD_ROOT).resolve()
    tenant_storage = (storage_root / str(business.id)).resolve()
    if tenant_storage.parent != storage_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Business storage target is invalid.')

    # A business owns an isolated Qdrant collection. Do not erase SQL data if
    # that collection cannot be removed first.
    try:
        rag_service.delete_business_collection(business.id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Knowledge vectors could not be removed. The business was not deleted.') from exc

    conversation_ids = db.query(Conversation.id).filter(Conversation.business_id == business.id).subquery()
    thread_ids = db.query(InternalThread.id).filter(InternalThread.business_id == business.id).subquery()
    document_ids = db.query(KnowledgeDocument.id).filter(KnowledgeDocument.business_id == business.id).subquery()

    business_name = business.name
    try:
        db.query(InternalMessage).filter(InternalMessage.thread_id.in_(thread_ids)).delete(synchronize_session=False)
        db.query(InternalThreadParticipant).filter(InternalThreadParticipant.thread_id.in_(thread_ids)).delete(synchronize_session=False)
        db.query(InternalThread).filter(InternalThread.business_id == business.id).delete(synchronize_session=False)
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        db.query(AgentReplyFeedback).filter(AgentReplyFeedback.business_id == business.id).delete(synchronize_session=False)
        db.query(FAQOpportunityFeedback).filter(FAQOpportunityFeedback.business_id == business.id).delete(synchronize_session=False)
        db.query(CustomerIdentity).filter(CustomerIdentity.business_id == business.id).delete(synchronize_session=False)
        db.query(Conversation).filter(Conversation.business_id == business.id).delete(synchronize_session=False)
        db.query(Customer).filter(Customer.business_id == business.id).delete(synchronize_session=False)
        db.query(KnowledgeIngestionJob).filter(KnowledgeIngestionJob.business_id == business.id).delete(synchronize_session=False)
        db.query(KnowledgeChunk).filter(KnowledgeChunk.business_id == business.id).delete(synchronize_session=False)
        db.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(document_ids)).delete(synchronize_session=False)
        db.query(Invitation).filter(Invitation.business_id == business.id).delete(synchronize_session=False)
        db.query(Integration).filter(Integration.business_id == business.id).delete(synchronize_session=False)
        db.query(User).filter(User.business_id == business.id).delete(synchronize_session=False)
        db.delete(business)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Business deletion could not be completed.') from exc

    storage_removed = True
    try:
        if tenant_storage.exists():
            shutil.rmtree(tenant_storage)
    except OSError:
        storage_removed = False
    return {
        'detail': business_name + ' was permanently deleted.',
        'business_id': business_id,
        'storage_removed': storage_removed,
    }


@router.post('/users', status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    role = payload.role.strip().lower()
    if role not in MANAGED_ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Choose business_admin, supervisor, or agent.')
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found.')
    email = str(payload.email).strip().lower()
    if db.query(User.id).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A user with this email already exists.')
    user = User(
        name=payload.name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=role,
        business_id=business.id,
        provider='platform_admin',
        email_verified=True,
        status='offline',
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'user': _user_json(user, business.name)}


@router.patch('/users/{user_id}')
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Platform administrator accounts cannot be changed here.')
    updates = payload.model_dump(exclude_unset=True)
    business = None
    if 'business_id' in updates:
        business = db.query(Business).filter(Business.id == updates['business_id']).first()
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Selected business not found.')
        user.business_id = business.id
    if 'email' in updates:
        email = str(updates['email']).strip().lower()
        duplicate = db.query(User.id).filter(User.email == email, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A user with this email already exists.')
        user.email = email
    if 'role' in updates:
        role = updates['role'].strip().lower()
        if role not in MANAGED_ROLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Choose business_admin, supervisor, or agent.')
        user.role = role
    if 'name' in updates:
        user.name = updates['name'].strip()
    if 'status' in updates:
        user.status = updates['status'].strip().lower()
    db.commit()
    db.refresh(user)
    if business is None and user.business_id:
        business = db.query(Business).filter(Business.id == user.business_id).first()
    return {'user': _user_json(user, business.name if business else None)}


@router.delete('/users/{user_id}')
def delete_user(
    user_id: int,
    payload: DeleteUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You cannot delete your own platform account.')
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='A platform administrator cannot be deleted here.')
    if str(payload.confirm_email).strip().lower() != user.email.lower():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Email confirmation does not match.')
    user_name = user.name or user.email
    try:
        db.query(Conversation).filter(Conversation.assigned_agent_id == user.id).update(
            {Conversation.assigned_agent_id: None}, synchronize_session=False
        )
        db.query(Message).filter(Message.sender_id == user.id).update(
            {Message.sender_id: None}, synchronize_session=False
        )
        db.query(CustomerIdentity).filter(CustomerIdentity.linked_by_user_id == user.id).update(
            {CustomerIdentity.linked_by_user_id: None}, synchronize_session=False
        )
        db.query(AgentReplyFeedback).filter(AgentReplyFeedback.agent_id == user.id).update(
            {AgentReplyFeedback.agent_id: None}, synchronize_session=False
        )
        db.query(InternalMessage).filter(InternalMessage.sender_id == user.id).delete(synchronize_session=False)
        db.query(InternalThreadParticipant).filter(InternalThreadParticipant.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='User deletion could not be completed.') from exc
    return {'detail': user_name + ' was permanently deleted.', 'user_id': user_id}


@router.get('/analytics')
def platform_analytics(
    days: int = Query(30, ge=1, le=366),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=days)
    messages_in_period = db.query(func.count(Message.id)).filter(Message.timestamp >= period_start).scalar() or 0
    conversations_in_period = db.query(func.count(Conversation.id)).filter(Conversation.created_at >= period_start).scalar() or 0
    channel_rows = db.query(
        Message.platform,
        func.count(Message.id).label('messages'),
    ).filter(
        Message.timestamp >= period_start,
    ).group_by(Message.platform).order_by(func.count(Message.id).desc()).all()
    channel_breakdown = [
        {'platform': row.platform or 'unknown', 'messages': int(row.messages or 0)}
        for row in channel_rows
    ]

    business_rows = []
    for business in db.query(Business).order_by(Business.created_at.desc()).all():
        conversation_ids = db.query(Conversation.id).filter(Conversation.business_id == business.id).subquery()
        business_rows.append({
            'id': business.id,
            'name': business.name,
            'is_active': bool(business.is_active),
            'users': db.query(func.count(User.id)).filter(User.business_id == business.id).scalar() or 0,
            'conversations': db.query(func.count(Conversation.id)).filter(Conversation.business_id == business.id).scalar() or 0,
            'messages': db.query(func.count(Message.id)).filter(Message.conversation_id.in_(conversation_ids)).scalar() or 0,
            'customers': db.query(func.count(Customer.id)).filter(Customer.business_id == business.id).scalar() or 0,
            'integrations': db.query(func.count(Integration.id)).filter(
                Integration.business_id == business.id,
                Integration.status == 'active',
            ).scalar() or 0,
            'ai_drafts': db.query(func.count(Message.id)).filter(
                Message.conversation_id.in_(conversation_ids),
                Message.ai_draft.isnot(None),
            ).scalar() or 0,
        })
    business_rows.sort(key=lambda item: item['messages'], reverse=True)

    return {
        'period': {'from': period_start.isoformat(), 'to': period_end.isoformat(), 'days': days},
        'totals': {
            'businesses': db.query(func.count(Business.id)).scalar() or 0,
            'active_businesses': db.query(func.count(Business.id)).filter(Business.is_active.is_(True)).scalar() or 0,
            'users': db.query(func.count(User.id)).scalar() or 0,
            'messages_in_period': messages_in_period,
            'conversations_in_period': conversations_in_period,
            'customers': db.query(func.count(Customer.id)).scalar() or 0,
            'connected_integrations': db.query(func.count(Integration.id)).filter(Integration.status == 'active').scalar() or 0,
            'knowledge_documents': db.query(func.count(KnowledgeDocument.id)).scalar() or 0,
        },
        'channels': channel_breakdown,
        'businesses': business_rows,
        'data_note': 'Platform analytics aggregate support activity. Revenue, conversion, and ROI require external order or CRM data.',
    }


@router.get("/stats")
def platform_stats(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    return {
        "total_businesses": db.query(func.count(Business.id)).scalar() or 0,
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "total_messages": db.query(func.count(Message.id)).scalar() or 0,
        "total_conversations": db.query(func.count(Conversation.id)).scalar() or 0,
        "total_customers": db.query(func.count(Customer.id)).scalar() or 0,
        "total_ai_drafts": db.query(func.count(Message.id)).filter(Message.ai_draft.isnot(None)).scalar() or 0,
        "total_documents": db.query(func.count(KnowledgeDocument.id)).scalar() or 0,
        "total_chunks": db.query(func.count(KnowledgeChunk.id)).scalar() or 0,
    }


@router.get("/businesses")
def all_businesses(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    result = []
    for business in db.query(Business).order_by(Business.created_at.desc()).all():
        owner = db.query(User).filter(
            User.business_id == business.id, User.role == "business_admin"
        ).first()
        result.append({
            "id": business.id,
            "name": business.name,
            "owner_email": owner.email if owner else None,
            "user_count": db.query(func.count(User.id)).filter(User.business_id == business.id).scalar() or 0,
            "message_count": db.query(func.count(Message.id)).join(Conversation).filter(Conversation.business_id == business.id).scalar() or 0,
            "conversation_count": db.query(func.count(Conversation.id)).filter(Conversation.business_id == business.id).scalar() or 0,
            "created_at": _iso(business.created_at),
            "is_active": business.is_active,
        })
    return result


@router.get("/users")
def all_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    businesses = {business.id: business.name for business in db.query(Business).all()}
    return [{
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "business_id": user.business_id,
        "business_name": businesses.get(user.business_id),
        "created_at": _iso(user.created_at),
    } for user in db.query(User).order_by(User.created_at.desc()).all()]


@router.get("/health")
def system_health(_current_user: User = Depends(require_super_admin)):
    from app.core.preflight import run_preflight
    return run_preflight()


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_super_admin),
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    total_businesses = db.query(func.count(Business.id)).scalar() or 0
    businesses_this_month = (
        db.query(func.count(Business.id))
        .filter(Business.created_at >= month_start)
        .scalar()
        or 0
    )
    total_users = db.query(func.count(User.id)).scalar() or 0
    users_this_month = (
        db.query(func.count(User.id)).filter(User.created_at >= month_start).scalar() or 0
    )
    total_ai_drafts = (
        db.query(func.count(Message.id)).filter(Message.ai_draft.isnot(None)).scalar() or 0
    )
    ai_drafts_this_week = (
        db.query(func.count(Message.id))
        .filter(Message.ai_draft.isnot(None), Message.timestamp >= week_start)
        .scalar()
        or 0
    )
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    active_integrations = (
        db.query(func.count(Integration.id)).filter(Integration.status == "active").scalar()
        or 0
    )
    open_conversations = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.status.in_(["open", "pending"]), Conversation.is_deleted.is_(False))
        .scalar()
        or 0
    )

    business_rows = (
        db.query(
            Business.id,
            Business.name,
            Business.is_active,
            Business.created_at,
            func.max(case((User.role == "business_admin", User.name), else_=None)).label("owner"),
            func.count(func.distinct(User.id)).label("users"),
            func.count(func.distinct(case((User.role.in_(["agent", "supervisor"]), User.id)))).label("agents"),
            func.count(func.distinct(Message.id)).label("messages"),
        )
        .outerjoin(User, User.business_id == Business.id)
        .outerjoin(Conversation, Conversation.business_id == Business.id)
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Business.id)
        .order_by(Business.created_at.desc())
        .all()
    )
    businesses = [
        {
            "id": row.id,
            "name": row.name,
            "owner": row.owner or "No business admin",
            "status": "active" if row.is_active else "inactive",
            "users": row.users,
            "agents": row.agents,
            "messages": row.messages,
            "joined": _iso(row.created_at),
        }
        for row in business_rows
    ]

    activities = []
    for business in db.query(Business).order_by(Business.created_at.desc()).limit(8):
        activities.append(
            {
                "action": "Business registered",
                "target": business.name,
                "type": "success",
                "timestamp": _iso(business.created_at),
            }
        )
    for user in db.query(User).order_by(User.created_at.desc()).limit(8):
        activities.append(
            {
                "action": "User joined",
                "target": user.name or user.email,
                "type": "info",
                "timestamp": _iso(user.created_at),
            }
        )
    for document in (
        db.query(KnowledgeDocument).order_by(KnowledgeDocument.uploaded_at.desc()).limit(8)
    ):
        activities.append(
            {
                "action": "Knowledge document uploaded",
                "target": document.filename,
                "type": "info" if document.status == "processing" else "success",
                "timestamp": _iso(document.uploaded_at),
            }
        )
    activities.sort(key=lambda item: item["timestamp"] or "", reverse=True)

    db_check_started = perf_counter()
    db.execute(func.now().select())
    db_latency_ms = round((perf_counter() - db_check_started) * 1000, 1)

    return {
        "stats": [
            {"key": "businesses", "label": "Total Businesses", "value": total_businesses, "change": f"+{businesses_this_month} this month"},
            {"key": "users", "label": "Total Users", "value": total_users, "change": f"+{users_this_month} this month"},
            {"key": "ai_drafts", "label": "AI Drafts Generated", "value": total_ai_drafts, "change": f"+{ai_drafts_this_week} this week"},
            {"key": "messages", "label": "Total Messages", "value": total_messages, "change": "All businesses"},
            {"key": "integrations", "label": "Active Integrations", "value": active_integrations, "change": "Connected and active"},
            {"key": "conversations", "label": "Conversations", "value": total_conversations, "change": f"{open_conversations} open or pending"},
        ],
        "businesses": businesses,
        "recent_activity": activities[:10],
        "database_stats": [
            {"label": "Total Messages", "value": total_messages},
            {"label": "Knowledge Documents", "value": db.query(func.count(KnowledgeDocument.id)).scalar() or 0},
            {"label": "Knowledge Chunks", "value": db.query(func.count(KnowledgeChunk.id)).scalar() or 0},
            {"label": "All Conversations", "value": total_conversations},
            {"label": "Open Conversations", "value": open_conversations},
        ],
        "system_health": [
            {"label": "FastAPI Backend", "status": "healthy", "detail": "Responding"},
            {"label": "PostgreSQL Database", "status": "healthy", "detail": f"{db_latency_ms} ms query"},
        ],
        "generated_at": now.isoformat(),
    }
