from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.business import Business
from app.models.integration import Integration
from app.prompts.customer_reply_prompt import build_system_prompt
from app.services.rag_service import RAGService
from app.services.webhook_service import find_business_for_recipient
from app.services.credential_service import encrypt_secret
from app.services.email_poller import build_email_poll_configs
from app.routers.integrations import oauth_callback, oauth_service
from jose import jwt


def test_webhook_recipient_routes_to_its_own_business():
    engine = create_engine("sqlite:///:memory:")
    Business.__table__.create(engine)
    Integration.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        first = Business(id=101, name="First Test Business")
        second = Business(id=202, name="Second Test Business")
        session.add_all([first, second])
        session.add_all([
            Integration(
                business_id=101,
                platform="facebook",
                page_id="page-first",
                access_token="token-first",
                status="active",
            ),
            Integration(
                business_id=202,
                platform="facebook",
                page_id="page-second",
                access_token="token-second",
                status="active",
            ),
        ])
        session.commit()

        assert find_business_for_recipient(
            session, "facebook", "page-first"
        ).id == 101
        assert find_business_for_recipient(
            session, "facebook", "page-second"
        ).id == 202
        assert find_business_for_recipient(
            session, "instagram", "page-second"
        ) is None
    finally:
        session.close()


def test_qdrant_retrieval_is_filtered_by_business(monkeypatch):
    collection = "multibusiness_isolation_test"
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )
    client.upsert(
        collection_name=collection,
        points=[
            PointStruct(
                id=1,
                vector=[1.0, 0.0],
                payload={
                    "business_id": 101,
                    "content": "FIRST_BUSINESS_SECRET_POLICY",
                    "filename": "first.pdf",
                },
            ),
            PointStruct(
                id=2,
                vector=[1.0, 0.0],
                payload={
                    "business_id": 202,
                    "content": "SECOND_BUSINESS_SECRET_POLICY",
                    "filename": "second.pdf",
                },
            ),
        ],
    )
    service = RAGService()
    service._qdrant = client
    service._collection_initialized = True
    monkeypatch.setattr(settings, "QDRANT_COLLECTION_NAME", collection)
    monkeypatch.setattr(service, "embed_text", lambda _: [1.0, 0.0])

    first_results = service.retrieve_chunks("same question", 101)
    second_results = service.retrieve_chunks("same question", 202)

    assert [item["content"] for item in first_results] == [
        "FIRST_BUSINESS_SECRET_POLICY"
    ]
    assert [item["content"] for item in second_results] == [
        "SECOND_BUSINESS_SECRET_POLICY"
    ]


def test_non_techsuru_prompt_does_not_inject_techsuru_policies():
    prompt = build_system_prompt(
        context="Acme only repairs musical instruments.",
        business_name="Acme Repairs",
    )
    assert "Acme Repairs" in prompt
    assert "TechSuru" not in prompt
    assert "Do not assume what this business sells" in prompt


def test_email_poller_builds_one_config_per_business(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Business.__table__.create(engine)
    Integration.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        session.add_all([
            Business(id=301, name="Mail Business One"),
            Business(id=302, name="Mail Business Two"),
        ])
        session.add_all([
            Integration(
                business_id=301,
                platform="email",
                page_id="one@example.com",
                access_token="encrypted-app-password",
                status="active",
                metadata_json={
                    "email": "one@example.com",
                    "password_encrypted": encrypt_secret("password-one"),
                    "imap_host": "imap.one.example",
                    "imap_port": 993,
                },
            ),
            Integration(
                business_id=302,
                platform="email",
                page_id="two@example.com",
                access_token="encrypted-app-password",
                status="active",
                metadata_json={
                    "email": "two@example.com",
                    "password_encrypted": encrypt_secret("password-two"),
                    "imap_host": "imap.two.example",
                    "imap_port": 1993,
                },
            ),
        ])
        session.commit()
        monkeypatch.setattr(settings, "TECHSURU_IMAP_EMAIL", None)
        monkeypatch.setattr(settings, "TECHSURU_IMAP_PASSWORD", None)

        configs = build_email_poll_configs(session)
        assert configs == [
            {
                "business_id": 301,
                "imap_email": "one@example.com",
                "imap_password": "password-one",
                "imap_host": "imap.one.example",
                "imap_port": 993,
            },
            {
                "business_id": 302,
                "imap_email": "two@example.com",
                "imap_password": "password-two",
                "imap_host": "imap.two.example",
                "imap_port": 1993,
            },
        ]
    finally:
        session.close()


@pytest.mark.asyncio
async def test_facebook_oauth_callback_stores_page_identity(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Business.__table__.create(engine)
    Integration.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        session.add(Business(id=401, name="OAuth Test Business"))
        session.commit()
        state = jwt.encode(
            {
                "type": "integration_oauth",
                "business_id": 401,
                "platform": "facebook",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        monkeypatch.setattr(
            oauth_service,
            "exchange_code_for_token",
            AsyncMock(return_value={"access_token": "user-token", "expires_in": 3600}),
        )
        monkeypatch.setattr(
            oauth_service,
            "discover_facebook_pages",
            AsyncMock(return_value=[
                {
                    "id": "second-business-page",
                    "name": "Second Business Page",
                    "access_token": "second-page-token",
                }
            ]),
        )
        monkeypatch.setattr(
            oauth_service,
            "enable_webhook_for_page",
            AsyncMock(return_value=True),
        )

        response = await oauth_callback(
            "facebook",
            "authorization-code",
            state,
            session,
        )
        integration = session.query(Integration).one()
        assert response.status_code == 307
        assert integration.business_id == 401
        assert integration.page_id == "second-business-page"
        assert integration.page_name == "Second Business Page"
        assert integration.access_token == "second-page-token"
    finally:
        session.close()
