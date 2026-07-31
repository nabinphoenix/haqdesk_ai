from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.invitation import Invitation
from app.models.user import User
from app.routers import team


client = TestClient(app)
PASSWORD = "SecureTest123!"


@pytest.fixture
def tenant(monkeypatch):
    monkeypatch.setattr(team, "_get_mail_config", lambda: None)
    suffix = uuid4().hex
    context = {
        "business_name": f"Permission Test Business {suffix}",
        "admin_email": f"admin-{suffix}@example.com",
        "agent_email": f"agent-{suffix}@example.com",
        "revoked_email": f"revoked-{suffix}@example.com",
        "expired_email": f"expired-{suffix}@example.com",
        "wrong_email": f"wrong-{suffix}@example.com",
    }
    yield context

    db = SessionLocal()
    business = db.query(Business).filter(Business.name == context["business_name"]).first()
    if business:
        db.query(Conversation).filter(Conversation.business_id == business.id).delete(
            synchronize_session=False
        )
        db.query(Customer).filter(Customer.business_id == business.id).delete(
            synchronize_session=False
        )
        db.query(Invitation).filter(Invitation.business_id == business.id).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.business_id == business.id).delete(
            synchronize_session=False
        )
        db.delete(business)
    db.commit()
    db.close()


def register_and_login_admin(context):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Permission Test Admin",
            "email": context["admin_email"],
            "password": PASSWORD,
            "business_name": context["business_name"],
        },
    )
    assert register.status_code == 200, register.text
    login = client.post(
        "/api/v1/auth/token",
        data={"username": context["admin_email"], "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    return register.json(), login.json()["access_token"]


def create_invite(admin_token, email):
    response = client.post(
        "/api/v1/team/invite",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": email, "role": "agent"},
    )
    assert response.status_code == 200, response.text
    token = parse_qs(urlparse(response.json()["invite_url"]).query)["token"][0]
    return response.json(), token


def accept_invite(token, email, name="Permission Test Agent"):
    return client.post(
        "/api/v1/team/accept-invite",
        json={
            "invite_token": token,
            "name": name,
            "email": email,
            "password": PASSWORD,
        },
    )


def test_db_backed_invitation_and_agent_permissions(tenant):
    admin, admin_token = register_and_login_admin(tenant)
    invitation_payload, invitation_token = create_invite(admin_token, tenant["agent_email"])

    db = SessionLocal()
    invitation = db.query(Invitation).filter(Invitation.id == invitation_payload["id"]).one()
    assert invitation.business_id == admin["business_id"]
    assert invitation.accepted is False
    assert invitation.revoked is False
    db.close()

    accepted = accept_invite(invitation_token, tenant["agent_email"])
    assert accepted.status_code == 200, accepted.text

    db = SessionLocal()
    agent = db.query(User).filter(User.email == tenant["agent_email"]).one()
    invitation = db.query(Invitation).filter(Invitation.id == invitation_payload["id"]).one()
    assert agent.role == "agent"
    assert agent.business_id == admin["business_id"]
    assert invitation.accepted is True

    customer = Customer(
        business_id=admin["business_id"],
        platform="manual",
        platform_user_id=f"permission-test-{uuid4().hex}",
        display_name="Permission Test Customer",
    )
    db.add(customer)
    db.flush()
    conversation = Conversation(
        business_id=admin["business_id"],
        customer_id=customer.id,
        status="open",
        priority="medium",
    )
    db.add(conversation)
    db.commit()
    conversation_id = conversation.id
    admin_id = admin["id"]
    db.close()

    agent_login = client.post(
        "/api/v1/auth/token",
        data={"username": tenant["agent_email"], "password": PASSWORD},
    )
    assert agent_login.status_code == 200
    agent_token = agent_login.json()["access_token"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}

    members = client.get("/api/v1/team/members", headers=agent_headers)
    assert members.status_code == 200
    assert {member["email"] for member in members.json()} == {
        tenant["admin_email"],
        tenant["agent_email"],
    }

    denied_requests = [
        client.post(
            "/api/v1/team/invite",
            headers=agent_headers,
            json={"email": tenant["wrong_email"], "role": "agent"},
        ),
        client.delete(f"/api/v1/team/members/{admin_id}", headers=agent_headers),
        client.patch(
            "/api/v1/settings/business",
            headers=agent_headers,
            json={"name": "Unauthorized Rename"},
        ),
        client.post(
            "/api/v1/integrations/email/configure",
            headers=agent_headers,
            json={"email": "support@example.com", "app_password": "not-used"},
        ),
        client.get("/api/v1/integrations/facebook/connect", headers=agent_headers),
        client.post(
            "/api/v1/knowledge/upload",
            headers=agent_headers,
            files={"file": ("test.txt", b"test", "text/plain")},
        ),
        client.delete("/api/v1/knowledge/documents/999999", headers=agent_headers),
        client.patch(
            "/api/v1/knowledge/chunks/999999",
            headers=agent_headers,
            json={"content": "unauthorized"},
        ),
        client.delete(f"/api/v1/inbox/conversations/{conversation_id}", headers=agent_headers),
        client.post(f"/api/v1/inbox/conversations/{conversation_id}/restore", headers=agent_headers),
    ]
    assert [response.status_code for response in denied_requests] == [403] * len(denied_requests)

    priority = client.patch(
        f"/api/v1/inbox/conversations/{conversation_id}",
        headers=agent_headers,
        json={"priority": "urgent"},
    )
    pending = client.patch(
        f"/api/v1/inbox/conversations/{conversation_id}",
        headers=agent_headers,
        json={"status": "pending"},
    )
    resolved = client.patch(
        f"/api/v1/inbox/conversations/{conversation_id}",
        headers=agent_headers,
        json={"status": "resolved"},
    )
    closed = client.patch(
        f"/api/v1/inbox/conversations/{conversation_id}",
        headers=agent_headers,
        json={"status": "closed"},
    )
    assert priority.status_code == 200
    assert pending.status_code == 200
    assert resolved.status_code == 403
    assert closed.status_code == 403

    reused = accept_invite(invitation_token, tenant["agent_email"])
    assert reused.status_code == 400
    assert reused.json()["detail"] == "This invitation has already been used"


def test_invitation_revoke_expire_wrong_email_and_deprecation(tenant):
    admin, admin_token = register_and_login_admin(tenant)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    revoked_payload, revoked_token = create_invite(admin_token, tenant["revoked_email"])
    revoke = client.delete(
        f"/api/v1/team/invitations/{revoked_payload['id']}",
        headers=admin_headers,
    )
    assert revoke.status_code == 200
    assert client.get(
        "/api/v1/team/validate-invite", params={"token": revoked_token}
    ).json()["detail"] == "This invitation has been revoked"
    assert accept_invite(revoked_token, tenant["revoked_email"]).status_code == 400

    db = SessionLocal()
    expired_token = str(uuid4())
    db.add(
        Invitation(
            business_id=admin["business_id"],
            email=tenant["expired_email"],
            role="agent",
            token=expired_token,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
    )
    db.commit()
    db.close()
    expired = client.get("/api/v1/team/validate-invite", params={"token": expired_token})
    assert expired.status_code == 400
    assert expired.json()["detail"] == "This invitation has expired"

    _, wrong_email_token = create_invite(admin_token, tenant["wrong_email"])
    wrong_email = accept_invite(wrong_email_token, tenant["agent_email"])
    assert wrong_email.status_code == 400
    assert "Please use that email" in wrong_email.json()["detail"]

    deprecated = client.post("/api/v1/team/invite-link")
    assert deprecated.status_code == 410
