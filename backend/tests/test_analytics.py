from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.message import Message
from app.models.user import User
from app.routers.auth import create_access_token


client = TestClient(app)


def auth_headers(user: User):
    token = create_access_token({"sub": user.email, "role": user.role, "name": user.name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analytics_data():
    suffix = uuid4().hex
    db = SessionLocal()
    business = Business(name=f"Analytics Business {suffix}")
    other_business = Business(name=f"Analytics Other {suffix}")
    empty_business = Business(name=f"Analytics Empty {suffix}")
    db.add_all([business, other_business, empty_business])
    db.flush()

    users = {
        "admin": User(name="Analytics Admin", email=f"analytics-admin-{suffix}@example.com", hashed_password="unused", role="business_admin", business_id=business.id),
        "supervisor": User(name="Analytics Supervisor", email=f"analytics-supervisor-{suffix}@example.com", hashed_password="unused", role="supervisor", business_id=business.id),
        "agent": User(name="Analytics Agent", email=f"analytics-agent-{suffix}@example.com", hashed_password="unused", role="agent", business_id=business.id),
        "other_agent": User(name="Other Agent", email=f"analytics-other-{suffix}@example.com", hashed_password="unused", role="agent", business_id=other_business.id),
        "empty_admin": User(name="Empty Admin", email=f"analytics-empty-{suffix}@example.com", hashed_password="unused", role="business_admin", business_id=empty_business.id),
        "super_admin": User(name="Platform Admin", email=f"analytics-root-{suffix}@example.com", hashed_password="unused", role="super_admin", business_id=None),
    }
    db.add_all(users.values())
    db.flush()

    facebook_customer = Customer(business_id=business.id, platform="facebook", platform_user_id=f"fb-{suffix}", display_name="Facebook Customer")
    instagram_customer = Customer(business_id=business.id, platform="instagram", platform_user_id=f"ig-{suffix}", display_name="Instagram Customer")
    other_customer = Customer(business_id=other_business.id, platform="facebook", platform_user_id=f"other-{suffix}", display_name="Other Customer")
    db.add_all([facebook_customer, instagram_customer, other_customer])
    db.flush()

    current_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    conversations = {
        "facebook": Conversation(business_id=business.id, customer_id=facebook_customer.id, assigned_agent_id=users["agent"].id, status="open", priority="urgent", is_deleted=False, created_at=current_start + timedelta(hours=2)),
        "instagram": Conversation(business_id=business.id, customer_id=instagram_customer.id, status="pending", priority="medium", is_deleted=False, created_at=current_start + timedelta(days=1)),
        "deleted": Conversation(business_id=business.id, customer_id=facebook_customer.id, status="resolved", priority="low", is_deleted=True, deleted_at=current_start + timedelta(days=2), created_at=current_start + timedelta(days=2)),
        "previous": Conversation(business_id=business.id, customer_id=facebook_customer.id, status="resolved", priority="medium", is_deleted=False, created_at=current_start - timedelta(days=2)),
        "other": Conversation(business_id=other_business.id, customer_id=other_customer.id, status="open", priority="urgent", is_deleted=False, created_at=current_start + timedelta(hours=2)),
    }
    db.add_all(conversations.values())
    db.flush()

    db.add_all([
        Message(conversation_id=conversations["facebook"].id, sender_type="customer", content="Need help", platform="facebook", sentiment="negative", timestamp=current_start + timedelta(hours=3), ai_draft="Draft"),
        Message(conversation_id=conversations["facebook"].id, sender_type="agent", sender_id=users["agent"].id, content="Reply", platform="facebook", timestamp=current_start + timedelta(hours=4)),
        Message(conversation_id=conversations["instagram"].id, sender_type="customer", content="Thanks", platform="instagram", sentiment="positive", timestamp=current_start + timedelta(days=1, hours=2)),
        Message(conversation_id=conversations["deleted"].id, sender_type="customer", content="Deleted", platform="facebook", sentiment="neutral", timestamp=current_start + timedelta(days=2, hours=1)),
        Message(conversation_id=conversations["previous"].id, sender_type="customer", content="Previous", platform="facebook", sentiment="neutral", timestamp=current_start - timedelta(days=2, hours=-1)),
        Message(conversation_id=conversations["other"].id, sender_type="customer", content="Other tenant", platform="facebook", sentiment="negative", timestamp=current_start + timedelta(hours=3)),
    ])
    document = KnowledgeDocument(business_id=business.id, filename="analytics.txt", status="ready", uploaded_at=current_start + timedelta(hours=1))
    db.add(document)
    db.flush()
    db.add(KnowledgeChunk(business_id=business.id, document_id=document.id, content="Knowledge", page_number=1))
    db.commit()

    ids = {"business": business.id, "other_business": other_business.id, "empty_business": empty_business.id}
    detached_users = {}
    for key, user in users.items():
        db.refresh(user)
        detached_users[key] = User(id=user.id, email=user.email, name=user.name, role=user.role, business_id=user.business_id)
    db.close()
    yield {"users": detached_users, "ids": ids, "from": current_start, "to": current_start + timedelta(days=3)}

    db = SessionLocal()
    business_ids = list(ids.values())
    conversation_ids = [row[0] for row in db.query(Conversation.id).filter(Conversation.business_id.in_(business_ids)).all()]
    document_ids = [row[0] for row in db.query(KnowledgeDocument.id).filter(KnowledgeDocument.business_id.in_(business_ids)).all()]
    if conversation_ids:
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
    if document_ids:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id.in_(document_ids)).delete(synchronize_session=False)
    db.query(KnowledgeDocument).filter(KnowledgeDocument.business_id.in_(business_ids)).delete(synchronize_session=False)
    db.query(Conversation).filter(Conversation.business_id.in_(business_ids)).delete(synchronize_session=False)
    db.query(Customer).filter(Customer.business_id.in_(business_ids)).delete(synchronize_session=False)
    db.query(User).filter(User.email.like(f"%{suffix}%")).delete(synchronize_session=False)
    db.query(Business).filter(Business.id.in_(business_ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def params(data, **extra):
    value = {
        "from": data["from"].isoformat(),
        "to": data["to"].isoformat(),
        "timezone": "UTC",
    }
    value.update(extra)
    return value


def test_analytics_authentication_and_roles(analytics_data):
    assert client.get("/api/v1/analytics/summary").status_code == 401
    assert client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["agent"])).status_code == 403
    assert client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["supervisor"])).status_code == 200
    assert client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["admin"])).status_code == 200
    super_response = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["super_admin"]))
    assert super_response.status_code == 403
    assert "business context" in super_response.json()["detail"]


def test_tenant_isolation_and_empty_tenant(analytics_data):
    response = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data))
    assert response.status_code == 200
    assert response.json()["total_conversations"] == 2
    assert response.json()["total_messages"] == 3
    empty = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["empty_admin"]), params=params(analytics_data))
    assert empty.status_code == 200
    assert empty.json()["total_conversations"] == 0
    assert empty.json()["platform_breakdown"] == {}


@pytest.mark.parametrize("query", [
    {"from": "2026-01-03T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
    {"from": "2024-01-01T00:00:00Z", "to": "2026-01-03T00:00:00Z"},
    {"platform": "tiktok"},
    {"status": "unknown"},
    {"priority": "extreme"},
    {"timezone": "Mars/Olympus"},
])
def test_filter_validation(analytics_data, query):
    base = params(analytics_data)
    base.update(query)
    response = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["admin"]), params=base)
    assert response.status_code == 422


def test_cross_tenant_agent_filter_is_safe(analytics_data):
    response = client.get(
        "/api/v1/analytics/summary",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, agent_id=analytics_data["users"]["other_agent"].id),
    )
    assert response.status_code == 422
    assert "not available" in response.json()["detail"]


def test_deleted_platform_status_and_priority_filters(analytics_data):
    headers = auth_headers(analytics_data["users"]["admin"])
    base = client.get("/api/v1/analytics/summary", headers=headers, params=params(analytics_data)).json()
    included = client.get("/api/v1/analytics/summary", headers=headers, params=params(analytics_data, include_deleted="true")).json()
    facebook = client.get("/api/v1/analytics/summary", headers=headers, params=params(analytics_data, platform="facebook")).json()
    pending = client.get("/api/v1/analytics/summary", headers=headers, params=params(analytics_data, status="pending")).json()
    urgent = client.get("/api/v1/analytics/summary", headers=headers, params=params(analytics_data, priority="urgent")).json()
    assert (base["total_conversations"], base["total_messages"]) == (2, 3)
    assert (included["total_conversations"], included["total_messages"]) == (3, 4)
    assert facebook["platform_breakdown"] == {"facebook": 1}
    assert pending["total_conversations"] == 1
    assert urgent["total_conversations"] == 1


def test_comparison_and_zero_previous_percentage(analytics_data):
    response = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()
    conversations = response["metrics"]["total_conversations"]
    documents = response["metrics"]["knowledge_documents"]
    assert conversations["previous_value"] == 1
    assert conversations["absolute_change"] == 1
    assert conversations["percentage_change"] == 100.0
    assert documents["previous_value"] == 0
    assert documents["percentage_change"] is None


def test_grouping_and_sentiment(analytics_data):
    response = client.get("/api/v1/analytics/summary", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()
    assert response["platform_conversation_distribution"] == {"facebook": 1, "instagram": 1}
    assert response["sentiment_distribution"] == {"negative": 1, "positive": 1}


def test_zero_filled_buckets_and_timezone_boundaries(analytics_data):
    headers = auth_headers(analytics_data["users"]["admin"])
    trend = client.get("/api/v1/analytics/message-trend", headers=headers, params=params(analytics_data)).json()
    all_points = trend["series"][0]["points"]
    assert trend["bucket"] == "day"
    assert [point["value"] for point in all_points] == [2, 1, 0]

    kathmandu = client.get(
        "/api/v1/analytics/message-trend",
        headers=headers,
        params=params(analytics_data, timezone="Asia/Kathmandu"),
    ).json()
    assert kathmandu["series"][0]["points"][0]["start"].endswith("+05:45")


def test_csv_export_is_filtered_and_downloadable(analytics_data):
    response = client.get(
        "/api/v1/analytics/export",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, platform="facebook"),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.text.startswith("\ufeffHaqDesk AI Analytics Report")
    assert "platform,facebook" in response.text
    assert "Summary metrics" in response.text
    assert "Message volume trend" in response.text


def test_csv_export_uses_analytics_role_and_tenant_guards(analytics_data):
    assert client.get(
        "/api/v1/analytics/export",
        headers=auth_headers(analytics_data["users"]["agent"]),
    ).status_code == 403
    empty = client.get(
        "/api/v1/analytics/export",
        headers=auth_headers(analytics_data["users"]["empty_admin"]),
        params=params(analytics_data),
    )
    assert empty.status_code == 200
    assert "total_conversations,0" in empty.text


def test_pdf_export_is_valid_filtered_and_downloadable(analytics_data):
    from io import BytesIO
    from pypdf import PdfReader

    response = client.get(
        "/api/v1/analytics/export",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, platform="facebook", format="pdf"),
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].endswith('.pdf"')
    assert response.content.startswith(b"%PDF")
    reader = PdfReader(BytesIO(response.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "HaqDesk AI" in text
    assert "Analytics Report" in text
    assert "Platform" in text
    assert "Facebook" in text
    assert "Summary metrics" in text


def test_export_rejects_unknown_format(analytics_data):
    response = client.get(
        "/api/v1/analytics/export",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, format="xlsx"),
    )
    assert response.status_code == 422
