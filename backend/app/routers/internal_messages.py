from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.dependencies import get_current_user
from app.models.internal_messaging import InternalMessage, InternalThread, InternalThreadParticipant
from app.models.user import User

router = APIRouter(prefix="/internal-messages", tags=["internal-messages"])
ALLOWED_ROLES = {"business_admin", "supervisor", "agent"}
RECIPIENT_ROLES = {
    "business_admin": {"supervisor", "agent"},
    "supervisor": {"business_admin", "agent"},
    "agent": {"business_admin", "supervisor"},
}


class ThreadCreate(BaseModel):
    recipient_id: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


def require_messaging_user(user: User) -> None:
    if user.role not in ALLOWED_ROLES or not user.business_id:
        raise HTTPException(403, "Internal messaging is unavailable for this account")


def participant_thread(db: Session, user: User, thread_id: int) -> InternalThread:
    # Both tenant and membership are part of this query. A guessed foreign-tenant
    # thread ID is therefore indistinguishable from a missing thread.
    thread = (db.query(InternalThread).join(InternalThreadParticipant)
        .filter(InternalThread.id == thread_id,
                InternalThread.business_id == user.business_id,
                InternalThreadParticipant.user_id == user.id).first())
    if not thread:
        raise HTTPException(404, "Thread not found")
    return thread


def user_json(user: User):
    return {"id": user.id, "name": user.name, "role": user.role, "avatar_url": user.avatar_url}


def message_json(message: InternalMessage, sender: User):
    return {"id": message.id, "thread_id": message.thread_id, "sender": user_json(sender),
            "content": message.content, "created_at": message.created_at.isoformat()}


@router.get("/recipients")
def recipients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_messaging_user(current_user)
    return [user_json(u) for u in db.query(User).filter(
        User.business_id == current_user.business_id,
        User.role.in_(RECIPIENT_ROLES[current_user.role]),
        User.id != current_user.id,
    ).order_by(User.name).all()]


@router.post("/threads", status_code=201)
def create_thread(body: ThreadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_messaging_user(current_user)
    recipient = db.query(User).filter(User.id == body.recipient_id,
        User.business_id == current_user.business_id,
        User.role.in_(RECIPIENT_ROLES[current_user.role])).first()
    if not recipient:
        raise HTTPException(403, "Recipient is not permitted")
    mine = db.query(InternalThreadParticipant.thread_id).filter(InternalThreadParticipant.user_id == current_user.id).subquery()
    existing = (db.query(InternalThread).join(InternalThreadParticipant)
        .filter(InternalThread.business_id == current_user.business_id,
                InternalThread.id.in_(mine), InternalThreadParticipant.user_id == recipient.id).first())
    if existing:
        return {"id": existing.id}
    thread = InternalThread(business_id=current_user.business_id)
    db.add(thread); db.flush()
    db.add_all([InternalThreadParticipant(thread_id=thread.id, user_id=current_user.id),
                InternalThreadParticipant(thread_id=thread.id, user_id=recipient.id)])
    db.commit(); db.refresh(thread)
    return {"id": thread.id}


@router.get("/threads")
def list_threads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_messaging_user(current_user)
    threads = (db.query(InternalThread).join(InternalThreadParticipant)
        .filter(InternalThread.business_id == current_user.business_id,
                InternalThreadParticipant.user_id == current_user.id)
        .order_by(InternalThread.updated_at.desc()).all())
    result = []
    for thread in threads:
        members = (db.query(User).join(InternalThreadParticipant, InternalThreadParticipant.user_id == User.id)
                   .filter(InternalThreadParticipant.thread_id == thread.id, User.business_id == current_user.business_id).all())
        last = db.query(InternalMessage).filter(InternalMessage.thread_id == thread.id).order_by(InternalMessage.id.desc()).first()
        membership = db.query(InternalThreadParticipant).filter_by(thread_id=thread.id, user_id=current_user.id).first()
        unread = db.query(func.count(InternalMessage.id)).filter(InternalMessage.thread_id == thread.id,
            InternalMessage.sender_id != current_user.id,
            InternalMessage.created_at > (membership.last_read_at or datetime(1970, 1, 1, tzinfo=timezone.utc))).scalar()
        result.append({"id": thread.id, "participants": [user_json(u) for u in members if u.id != current_user.id],
                       "last_message": last.content if last else None, "updated_at": thread.updated_at.isoformat(), "unread_count": unread})
    return result


@router.get("/threads/{thread_id}/messages")
def history(thread_id: int, before_id: int | None = None, limit: int = Query(50, ge=1, le=100),
            db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    participant_thread(db, current_user, thread_id)
    query = db.query(InternalMessage, User).join(User, User.id == InternalMessage.sender_id).filter(InternalMessage.thread_id == thread_id)
    if before_id: query = query.filter(InternalMessage.id < before_id)
    rows = query.order_by(InternalMessage.id.desc()).limit(limit).all()
    return [message_json(m, u) for m, u in reversed(rows)]


@router.post("/threads/{thread_id}/messages", status_code=201)
async def send_message(thread_id: int, body: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    thread = participant_thread(db, current_user, thread_id)
    content = body.content.strip()
    if not content: raise HTTPException(422, "Message cannot be blank")
    message = InternalMessage(thread_id=thread.id, sender_id=current_user.id, content=content)
    thread.updated_at = datetime.now(timezone.utc)
    db.add(message); db.commit(); db.refresh(message)
    payload = {"type": "message", "message": message_json(message, current_user)}
    member_ids = [x[0] for x in db.query(InternalThreadParticipant.user_id).filter_by(thread_id=thread.id).all()]
    await manager.broadcast(member_ids, payload)
    return payload["message"]


@router.post("/threads/{thread_id}/read")
def mark_read(thread_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    participant_thread(db, current_user, thread_id)
    membership = db.query(InternalThreadParticipant).filter_by(thread_id=thread_id, user_id=current_user.id).first()
    membership.last_read_at = datetime.now(timezone.utc); db.commit()
    return {"ok": True}


class ConnectionManager:
    def __init__(self): self.connections = defaultdict(set)
    async def connect(self, user_id, socket):
        await socket.accept(); self.connections[user_id].add(socket)
    def disconnect(self, user_id, socket):
        self.connections[user_id].discard(socket)
    async def broadcast(self, user_ids, payload):
        for uid in user_ids:
            for socket in list(self.connections[uid]):
                try: await socket.send_json(payload)
                except Exception: self.disconnect(uid, socket)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    db = SessionLocal()
    try:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user = db.query(User).filter(User.email == payload.get("sub")).first()
            if not user or user.role not in ALLOWED_ROLES or not user.business_id:
                await websocket.close(code=1008); return
        except JWTError:
            await websocket.close(code=1008); return
        await manager.connect(user.id, websocket)
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "ping": await websocket.send_json({"type": "pong"})
                elif data.get("type") == "send":
                    try:
                        thread = participant_thread(db, user, int(data.get("thread_id")))
                        content = str(data.get("content", "")).strip()
                        if not content or len(content) > 10000:
                            await websocket.send_json({"type": "error", "detail": "Message must contain 1-10000 characters"}); continue
                        message = InternalMessage(thread_id=thread.id, sender_id=user.id, content=content)
                        thread.updated_at = datetime.now(timezone.utc); db.add(message); db.commit(); db.refresh(message)
                        member_ids = [row[0] for row in db.query(InternalThreadParticipant.user_id).filter_by(thread_id=thread.id).all()]
                        await manager.broadcast(member_ids, {"type": "message", "message": message_json(message, user)})
                    except (HTTPException, TypeError, ValueError):
                        db.rollback(); await websocket.send_json({"type": "error", "detail": "Thread not found or access denied"})
        except WebSocketDisconnect:
            manager.disconnect(user.id, websocket)
    finally:
        db.close()
