"""Team management router: invite sending (admin-only) and public invite acceptance."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
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
from app.auth.utils import hash_password
from app.routers.auth import get_current_user, create_access_token

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
    current_user: User = Depends(get_current_user),
):
    """Create an invitation token, send an email, and return the invite URL."""
    if current_user.role not in (UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can send invitations")

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
            Invitation.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=400, detail="An active invitation already exists for this email")

    # Create the invitation
    token = str(uuid4())
    mapped_role = ROLE_MAP.get(role, UserRole.AGENT).value
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
    business_name = "HaqDesk AI"
    if current_user.business_id:
        biz = db.query(Business).filter(Business.id == current_user.business_id).first()
        if biz:
            business_name = biz.name

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


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC: Accept an invitation  (NO auth required)
# POST /api/v1/team/accept-invite
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/accept-invite")
async def accept_invite(request: Request, db: Session = Depends(get_db)):
    """
    Public endpoint -- no JWT required.
    Body: { token, name, email, password }
    Creates the user account and links them to the correct business.
    """
    payload = await request.json()
    token = payload.get("token", "").strip()
    name = payload.get("name", "").strip()
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "").strip()

    if not all([token, name, email, password]):
        raise HTTPException(status_code=400, detail="token, name, email, and password are required")

    # Find the invitation
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token")

    if invitation.accepted:
        raise HTTPException(status_code=400, detail="This invitation has already been used")

    # Handle timezone-aware/naive comparisons safely
    now = datetime.now(timezone.utc) if invitation.expires_at.tzinfo is not None else datetime.utcnow()
    if invitation.expires_at < now:
        raise HTTPException(status_code=400, detail="This invitation has expired")

    # Verify the email matches the invitation
    if invitation.email != email:
        raise HTTPException(status_code=400, detail="Email does not match the invitation")

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Verify the business exists
    business = db.query(Business).filter(Business.id == invitation.business_id).first()
    if not business:
        raise HTTPException(status_code=400, detail="The associated business no longer exists")

    # Map the role
    user_role = ROLE_MAP.get(invitation.role, UserRole.AGENT)
    if isinstance(user_role, str):
        user_role = UserRole(user_role)

    # Create the user
    hashed_password = hash_password(password)
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=user_role.value if isinstance(user_role, UserRole) else user_role,
        provider="local",
        email_verified=True,
        business_id=invitation.business_id,
    )
    db.add(new_user)

    # Mark invitation as accepted
    invitation.accepted = True

    db.commit()
    db.refresh(new_user)

    # Generate JWT so the new user is logged in immediately
    access_token = create_access_token(
        data={"sub": new_user.email, "role": new_user.role, "name": new_user.name}
    )

    logger.info(f"Invitation accepted: {email} joined business {business.name} as {user_role}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "business_id": new_user.business_id,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC: Validate an invitation token  (NO auth required)
# GET /api/v1/team/validate-invite?token=xxx
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/validate-invite")
async def validate_invite(token: str, db: Session = Depends(get_db)):
    """Check if an invite token is valid and return invite details."""
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token")

    if invitation.accepted:
        raise HTTPException(status_code=400, detail="This invitation has already been used")

    # Handle timezone-aware/naive comparisons safely
    now = datetime.now(timezone.utc) if invitation.expires_at.tzinfo is not None else datetime.utcnow()
    if invitation.expires_at < now:
        raise HTTPException(status_code=400, detail="This invitation has expired")

    business = db.query(Business).filter(Business.id == invitation.business_id).first()

    return {
        "email": invitation.email,
        "role": invitation.role,
        "business_name": business.name if business else "Unknown",
        "expires_at": invitation.expires_at.isoformat(),
    }


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

    return [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "status": m.status or "offline",
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "avatar_url": m.avatar_url,
        }
        for m in members
    ]


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN-ONLY: Remove a team member  (requires JWT)
# DELETE /api/v1/team/members/{user_id}
# ──────────────────────────────────────────────────────────────────────────────
@router.delete("/members/{user_id}")
async def remove_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a team member. Admins only, cannot remove yourself."""
    if current_user.role not in (UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can remove members")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")

    member = db.query(User).filter(User.id == user_id).first()
    if not member or member.business_id != current_user.business_id:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()

    return {"detail": f"Member {member.name} removed successfully"}
