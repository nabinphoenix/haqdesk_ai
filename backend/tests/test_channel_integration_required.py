import asyncio
import secrets

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.integration import Integration
from app.models.message import Message
from app.models.user import User
from app.routers.inbox import ReplyRequest, reply_to_conversation
from app.services import webhook_service


def _database():
    engine = create_engine("sqlite:///:memory:")
    for table in [
        Business.__table__,
        User.__table__,
        Customer.__table__,
        Conversation.__table__,
        Integration.__table__,
        Message.__table__,
    ]:
        table.create(engine)
    return sessionmaker(bind=engine)


def _tenant_records(session, *, auto_mode=False):
    values = [secrets.randbelow(1_000_000) + 1 for _ in range(5)]
    business_id, user_id, customer_id, conversation_id, message_id = values
    business = Business(
        id=business_id,
        name=f"Business {business_id}",
        ai_response_mode="auto" if auto_mode else "review",
    )
    user = User(
        id=user_id,
        business_id=business_id,
        name="Test Agent",
        email=f"agent-{user_id}@example.test",
        hashed_password="unused",
    )
    customer = Customer(
        id=customer_id,
        business_id=business_id,
        platform="facebook",
        platform_user_id=f"customer-{customer_id}",
        display_name="Test Customer",
    )
    conversation = Conversation(
        id=conversation_id,
        business_id=business_id,
        customer_id=customer_id,
    )
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        sender_type="customer",
        content="Please help",
        platform="facebook",
    )
    session.add_all([business, user, customer, conversation, message])
    session.commit()
    return business, user, conversation, message


def test_manual_send_without_integration_returns_409_and_saves_nothing(monkeypatch):
    factory = _database()
    session = factory()
    try:
        _business, user, conversation, _message = _tenant_records(session)
        initial_count = session.query(Message).count()
        monkeypatch.setattr(
            settings, "ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX", False
        )

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                reply_to_conversation(
                    conversation.id,
                    ReplyRequest(content="Agent response"),
                    session,
                    user,
                )
            )

        assert exc_info.value.status_code == 409
        assert "Connect your facebook account" in exc_info.value.detail
        assert session.query(Message).count() == initial_count
    finally:
        session.close()


def test_auto_send_without_integration_retains_draft_for_retry(monkeypatch):
    factory = _database()
    setup_session = factory()
    business, _user, conversation, message = _tenant_records(
        setup_session, auto_mode=True
    )
    business_id = business.id
    conversation_id = conversation.id
    message_id = message.id
    setup_session.close()

    async def generated_reply(**_kwargs):
        return {
            "answer": "A safe draft response.",
            "language_detected": "english",
            "metadata": {"fallback_used": False},
        }

    monkeypatch.setattr(webhook_service, "SessionLocal", factory)
    monkeypatch.setattr(webhook_service, "detect_sentiment", lambda _text: "neutral")
    monkeypatch.setattr(webhook_service.rag_service, "query", generated_reply)
    monkeypatch.setattr(
        settings, "ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX", False
    )

    asyncio.run(
        webhook_service.process_incoming_message_in_background(
            message_id, conversation_id, "Please help", business_id
        )
    )

    verify_session = factory()
    try:
        saved = verify_session.query(Message).filter(Message.id == message_id).one()
        automatic_messages = verify_session.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_type == "agent",
        ).all()
        assert "A safe draft response" in saved.ai_draft
        assert automatic_messages == []
    finally:
        verify_session.close()

def test_auto_send_records_the_reply_as_ai(monkeypatch):
    factory = _database()
    session = factory()
    try:
        business, _user, conversation, _message = _tenant_records(session, auto_mode=True)
        session.add(Integration(business_id=business.id, platform="facebook", page_id="page-1", access_token="token"))
        session.commit()

        async def accepted_by_platform(**_kwargs):
            return {"message_id": "platform-message-1"}

        monkeypatch.setattr(webhook_service.messaging_service, "send_message", accepted_by_platform)
        asyncio.run(
            webhook_service.dispatch_auto_ai_reply(
                session, conversation.id, business.id, "Automatic reply"
            )
        )

        automatic_reply = session.query(Message).filter(Message.content == "Automatic reply").one()
        assert automatic_reply.sender_type == "ai"
        assert automatic_reply.sender_id is None
        assert automatic_reply.ai_metadata["response_mode"] == "auto"
    finally:
        session.close()
