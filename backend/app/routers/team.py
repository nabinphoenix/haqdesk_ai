"""Team management router: invite sending (admin-only) and public invite acceptance."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import logging

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.invitation import Invitation
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.customer_identity import CustomerIdentity
from app.models.internal_messaging import InternalMessage, InternalThreadParticipant
from app.auth.utils import hash_password, pwd_context
from app.core.dependencies import get_current_user, require_business_admin

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Role mapping: frontend role names → backend UserRole enum ───
ROLE_MAP = {
    "Admin": UserRole.BUSINESS_ADMIN,
    "Supervisor": UserRole.SUPERVISOR,
    "Agent": UserRole.AGENT,
    "admin": UserRole.BUSINESS_ADMIN,
    "supervisor": UserRole.SUPERVISOR,
    "agent": UserRole.AGENT,
    "business_admin": UserRole.BUSINESS_ADMIN,
}

# ─── Role display names for emails ───
ROLE_DISPLAY = {
    "agent": "Agent",
    "supervisor": "Supervisor",
    "business_admin": "Admin",
    "Agent": "Agent",
    "Supervisor": "Supervisor",
    "Admin": "Admin",
}


# ─── Email configuration (lazy – only created when mail credentials exist) ───
def _get_mail_config() -> ConnectionConfig | None:
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


def _build_invite_email_html(
    business_name: str, role: str, invite_url: str
) -> str:
    """Build a polished HTML email body for the invitation."""
    role_label = ROLE_DISPLAY.get(role, role.title())
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0a1a;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a1a;padding:40px 0;">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0"
             style="background:#13132b;border:1px solid rgba(255,255,255,0.06);border-radius:16px;overflow:hidden;">

        <!-- Header bar -->
        <tr>
          <td style="padding:32px 40px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0"><tr>
              <td style="width:36px;height:36px;background:#6D4AE2;border-radius:10px;text-align:center;vertical-align:middle;">
                <span style="color:#fff;font-weight:bold;font-size:14px;">H</span>
              </td>
              <td style="padding-left:12px;">
                <span style="color:#fff;font-weight:700;font-size:15px;letter-spacing:-0.3px;">
                  HaqDesk <span style="color:#818CF8;">AI</span>
                </span>
              </td>
            </tr></table>
          </td>
        </tr>

        <!-- Main content -->
        <tr>
          <td style="padding:32px 40px;">
            <h1 style="margin:0 0 8px;color:#ffffff;font-size:22px;font-weight:800;letter-spacing:-0.5px;">
              You&rsquo;re invited to join {business_name}
            </h1>
            <p style="margin:0 0 24px;color:#9ca3af;font-size:14px;line-height:1.6;">
              You have been invited to join <strong style="color:#e5e7eb;">{business_name}</strong>
              on HaqDesk AI as a <strong style="color:#818CF8;">{role_label}</strong>.
            </p>

            <!-- Role badge -->
            <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              <tr>
                <td style="background:rgba(129,140,248,0.1);border:1px solid rgba(129,140,248,0.2);
                           border-radius:8px;padding:6px 14px;">
                  <span style="color:#818CF8;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;">
                    {role_label}
                  </span>
                </td>
              </tr>
            </table>

            <!-- CTA button -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr><td align="center" style="padding:4px 0 24px;">
                <a href="{invite_url}"
                   style="display:inline-block;background:#6D4AE2;color:#ffffff;
                          font-size:14px;font-weight:700;text-decoration:none;
                          padding:14px 40px;border-radius:12px;letter-spacing:0.3px;">
                  Accept Invitation
                </a>
              </td></tr>
            </table>

            <!-- Expiry note -->
            <p style="margin:0 0 6px;color:#6b7280;font-size:12px;line-height:1.5;">
              This link expires in <strong style="color:#9ca3af;">7 days</strong>.
              If you did not expect this invitation, you can safely ignore this email.
            </p>
            <p style="margin:12px 0 0;color:#6b7280;font-size:12px;line-height:1.5;">
              Sign in with your own HaqDesk account. Social channel passwords are never required.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid rgba(255,255,255,0.04);">
            <p style="margin:0;color:#4b5563;font-size:12px;">
              &mdash; HaqDesk AI Team
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN-ONLY: Send an invitation  (requires JWT)
# POST /api/v1/team/invite
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/invite")
async def send_invite(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin),
):
    """Create an invitation token, send an email, and return the invite URL."""
    payload = await request.json()
    email = payload.get("email", "").strip().lower()
    role = payload.get("role", "Agent")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Check for pending invite
    pending = (
        db.query(Invitation)
        .filter(
            Invitation.email == email,
            Invitation.accepted == False,
            Invitation.revoked == False,
            Invitation.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=400, detail="An active invitation already exists for this email")

    # Create the invitation
    token = str(uuid4())
    mapped_role = ROLE_MAP.get(role, UserRole.AGENT).value
    if mapped_role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=400, detail="Super Admin invitations are not allowed")
    business = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    invitation = Invitation(
        business_id=current_user.business_id,
        email=email,
        role=mapped_role,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Build the accept-invite URL for the frontend
    invite_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"

    # ── Resolve business name for the email ──
    business_name = business.name

    # ── Send invitation email (non-blocking) ──
    mail_conf = _get_mail_config()
    email_sent = False
    if mail_conf:
        html_body = _build_invite_email_html(business_name, mapped_role, invite_url)
        message = MessageSchema(
            subject="You're invited to join HaqDesk AI",
            recipients=[email],
            body=html_body,
            subtype=MessageType.html,
        )
        fm = FastMail(mail_conf)

        async def _send():
            try:
                await fm.send_message(message)
                logger.info(f"Invitation email sent to {email}")
            except Exception as exc:
                logger.error(f"Failed to send invitation email to {email}: {exc}")

        background_tasks.add_task(_send)
        email_sent = True
    else:
        logger.warning("Mail credentials not configured -- skipping invitation email")

    logger.info(f"Invitation created for {email} with role {role} by {current_user.email}")

    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role,
        "token": invitation.token,
        "invite_url": invite_url,
        "email_sent": email_sent,
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.post("/invite-link", status_code=status.HTTP_410_GONE)
def deprecated_invite_link():
    """Deprecated stateless invitation endpoint."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This invitation endpoint is deprecated. Use /api/v1/team/invite.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC: Accept an invitation  (NO auth required)
# POST /api/v1/team/accept-invite
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/accept-invite")
async def accept_invite(
    invite_token: str = Body(...),
    name: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db)
):
    email = email.strip().lower()
    name = name.strip()
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required")

    invitation = (
        db.query(Invitation)
        .filter(Invitation.token == invite_token)
        .with_for_update()
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    if invitation.revoked:
        raise HTTPException(status_code=400, detail="This invitation has been revoked")
    if invitation.accepted:
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    now = datetime.now(timezone.utc) if invitation.expires_at.tzinfo else datetime.utcnow()
    if invitation.expires_at < now:
        raise HTTPException(status_code=400, detail="This invitation has expired")
    if email != invitation.email.lower():
        raise HTTPException(
            status_code=400,
            detail=f"This invite was sent to {invitation.email}. Please use that email to accept.",
        )

    business = db.query(Business).filter(Business.id == invitation.business_id).first()
    if not business:
        raise HTTPException(status_code=400, detail="The invited business no longer exists")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(password)
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=invitation.role,
        business_id=invitation.business_id,
        provider="local",
        email_verified=True,
        status="offline",
    )
    db.add(new_user)
    invitation.accepted = True
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Account created successfully. You can now login.",
        "email": new_user.email,
        "role": new_user.role
    }


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC: Validate an invitation token  (NO auth required)
# GET /api/v1/team/validate-invite?token=xxx
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/validate-invite")
async def validate_invite(token: str, db: Session = Depends(get_db)):
    """Check a stored invitation's status and return its public details."""
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation token")
    if invitation.revoked:
        raise HTTPException(status_code=400, detail="This invitation has been revoked")
    if invitation.accepted:
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    now = datetime.now(timezone.utc) if invitation.expires_at.tzinfo else datetime.utcnow()
    if invitation.expires_at < now:
        raise HTTPException(status_code=400, detail="This invitation has expired")

    business = db.query(Business).filter(Business.id == invitation.business_id).first()
    if not business:
        raise HTTPException(status_code=400, detail="The invited business no longer exists")
    return {
        "email": invitation.email,
        "role": invitation.role,
        "business_name": business.name,
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.get("/invitations")
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin),
):
    invitations = (
        db.query(Invitation)
        .filter(Invitation.business_id == current_user.business_id)
        .order_by(Invitation.created_at.desc())
        .all()
    )
    return [
        {
            "id": invitation.id,
            "email": invitation.email,
            "role": invitation.role,
            "accepted": invitation.accepted,
            "revoked": invitation.revoked,
            "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
            "expires_at": invitation.expires_at.isoformat(),
        }
        for invitation in invitations
    ]


@router.delete("/invitations/{invitation_id}")
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin),
):
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.business_id == current_user.business_id,
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.accepted:
        raise HTTPException(status_code=400, detail="Accepted invitations cannot be revoked")
    invitation.revoked = True
    db.commit()
    return {"detail": "Invitation revoked"}


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN-ONLY: List team members  (requires JWT)
# GET /api/v1/team/members
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/members")
async def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all users that belong to the same business."""
    if not current_user.business_id:
        return []

    members = (
        db.query(User)
        .filter(User.business_id == current_user.business_id)
        .order_by(User.created_at.asc())
        .all()
    )

    online_cutoff = datetime.now(timezone.utc) - timedelta(seconds=90)

    def member_status(member):
        last_seen = member.last_seen_at
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        return "online" if last_seen and last_seen >= online_cutoff else "offline"

    return [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "status": member_status(m),
            "last_seen_at": m.last_seen_at.isoformat() if m.last_seen_at else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "avatar_url": m.avatar_url,
        }
        for m in members
    ]


@router.get("/metrics")
async def team_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return live presence and response-performance data for the team page."""
    if not current_user.business_id:
        return {"members": [], "summary": {}}

    now = datetime.now(timezone.utc)
    online_cutoff = now - timedelta(seconds=90)
    members = db.query(User).filter(
        User.business_id == current_user.business_id
    ).order_by(User.created_at.asc()).all()
    conversations = db.query(Conversation).filter(
        Conversation.business_id == current_user.business_id
    ).all()
    conversation_ids = [conversation.id for conversation in conversations]
    messages = (
        db.query(Message)
        .filter(Message.conversation_id.in_(conversation_ids))
        .order_by(Message.conversation_id.asc(), Message.timestamp.asc(), Message.id.asc())
        .all()
        if conversation_ids else []
    )

    assigned_counts = {member.id: 0 for member in members}
    for conversation in conversations:
        if conversation.assigned_agent_id in assigned_counts:
            assigned_counts[conversation.assigned_agent_id] += 1

    response_times = []
    auto_times = []
    review_times = []
    member_times = {member.id: [] for member in members}
    pending_customer_at = {}

    for message in messages:
        if message.sender_type == "customer":
            pending_customer_at.setdefault(message.conversation_id, message.timestamp)
            continue
        if message.sender_type not in {"agent", "ai"} or message.conversation_id not in pending_customer_at:
            continue

        customer_at = pending_customer_at.pop(message.conversation_id)
        if not customer_at or not message.timestamp:
            continue
        seconds = max(0.0, (message.timestamp - customer_at).total_seconds())
        response_times.append(seconds)

        metadata = message.ai_metadata if isinstance(message.ai_metadata, dict) else {}
        response_mode = metadata.get("response_mode")
        if message.sender_type == "ai" or response_mode == "auto" or (not response_mode and message.sender_id is None):
            auto_times.append(seconds)
        else:
            review_times.append(seconds)
            if message.sender_id in member_times:
                member_times[message.sender_id].append(seconds)

    def average(values):
        return round(sum(values) / len(values), 1) if values else None

    member_payload = []
    for member in members:
        last_seen = member.last_seen_at
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        is_online = bool(last_seen and last_seen >= online_cutoff)
        member_payload.append({
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "role": member.role,
            "status": "online" if is_online else "offline",
            "last_seen_at": last_seen.isoformat() if last_seen else None,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "avatar_url": member.avatar_url,
            "conversations": assigned_counts.get(member.id, 0),
            "avg_response_seconds": average(member_times.get(member.id, [])),
            "responses": len(member_times.get(member.id, [])),
        })

    business = db.query(Business).filter(Business.id == current_user.business_id).first()
    return {
        "members": member_payload,
        "summary": {
            "total_members": len(members),
            "online_members": sum(1 for member in member_payload if member["status"] == "online"),
            "avg_response_seconds": average(response_times),
            "auto_avg_response_seconds": average(auto_times),
            "review_avg_response_seconds": average(review_times),
            "responses_measured": len(response_times),
            "auto_responses": len(auto_times),
            "review_responses": len(review_times),
            "ai_drafts_used": sum(
                1 for message in messages
                if message.sender_type == "agent"
                and isinstance(message.ai_metadata, dict)
                and message.ai_metadata.get("ai_assisted") is True
            ),
            "ai_response_mode": business.ai_response_mode if business else "review",
            "roles_active": len({member.role for member in members}),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN-ONLY: Permanently delete a team member (business-admin only)
# DELETE /api/v1/team/members/{user_id}
# ──────────────────────────────────────────────────────────────────────────────
@router.delete("/members/{user_id}")
async def remove_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete an agent or supervisor from the current business."""
    if current_user.role != UserRole.BUSINESS_ADMIN.value:
        raise HTTPException(status_code=403, detail="Only the business admin can delete team members")
    if not current_user.business_id:
        raise HTTPException(status_code=403, detail="No business associated")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    member = db.query(User).filter(
        User.id == user_id,
        User.business_id == current_user.business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    if member.role not in (UserRole.AGENT.value, UserRole.SUPERVISOR.value):
        raise HTTPException(status_code=403, detail="Only agents and supervisors can be deleted")

    member_name = member.name or member.email
    try:
        # Keep customer conversations and replies, but remove the deleted user's identity.
        db.query(Conversation).filter(
            Conversation.business_id == current_user.business_id,
            Conversation.assigned_agent_id == member.id,
        ).update({Conversation.assigned_agent_id: None}, synchronize_session=False)
        db.query(Message).filter(Message.sender_id == member.id).update(
            {Message.sender_id: None}, synchronize_session=False
        )
        # Nullable audit references must be cleared before deleting the user.
        db.query(CustomerIdentity).filter(CustomerIdentity.linked_by_user_id == member.id).update(
            {CustomerIdentity.linked_by_user_id: None}, synchronize_session=False
        )
        # Internal messages have a non-null user foreign key, so remove only this
        # member's internal messages and participant memberships first.
        db.query(InternalMessage).filter(InternalMessage.sender_id == member.id).delete(
            synchronize_session=False
        )
        db.query(InternalThreadParticipant).filter(InternalThreadParticipant.user_id == member.id).delete(
            synchronize_session=False
        )
        db.delete(member)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to permanently delete team member")

    return {
        "detail": f"{member_name} was permanently deleted",
        "user_id": user_id,
        "status": "deleted",
    }
