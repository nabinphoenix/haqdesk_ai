from datetime import datetime, timedelta, timezone
from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.integration import Integration
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.message import Message
from app.models.user import User


router = APIRouter(prefix="/super-admin", tags=["super-admin"])


def _iso(value):
    return value.isoformat() if value else None


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
