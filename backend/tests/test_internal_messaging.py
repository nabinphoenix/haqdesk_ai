from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.business import Business
from app.models.internal_messaging import InternalMessage, InternalThread, InternalThreadParticipant
from app.models.user import User
from app.routers.auth import create_access_token
import app.routers.internal_messages as messaging_router


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)


def auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.email, 'role': user.role, 'name': user.name})}"}


def test_live_delivery_tenant_isolation_and_reconnect_history():
    Base.metadata.create_all(engine)
    print("EVIDENCE setup: two businesses, admin + two agents")
    db = TestSession()
    one, two = Business(name="Messaging Tenant One"), Business(name="Messaging Tenant Two")
    db.add_all([one, two]); db.flush()
    admin = User(name="Admin One", email="msg-admin@example.test", hashed_password="x", role="business_admin", business_id=one.id)
    agent = User(name="Agent One", email="msg-agent@example.test", hashed_password="x", role="agent", business_id=one.id)
    outsider = User(name="Agent Two", email="msg-outsider@example.test", hashed_password="x", role="agent", business_id=two.id)
    db.add_all([admin, agent, outsider]); db.commit()
    app.dependency_overrides[get_db] = lambda: (yield db)
    messaging_router.SessionLocal = TestSession
    client = TestClient(app)
    try:
        # Foreign-tenant users are not discoverable and cannot be selected directly.
        recipients = client.get("/api/v1/internal-messages/recipients", headers=auth(admin))
        assert recipients.status_code == 200
        assert [p["id"] for p in recipients.json()] == [agent.id]
        denied = client.post("/api/v1/internal-messages/threads", headers=auth(admin), json={"recipient_id": outsider.id})
        print("EVIDENCE cross-business thread create:", denied.status_code, denied.json())
        assert denied.status_code == 403

        made = client.post("/api/v1/internal-messages/threads", headers=auth(admin), json={"recipient_id": agent.id})
        assert made.status_code == 201
        thread_id = made.json()["id"]
        # A real authenticated WebSocket persists and receives a message live.
        agent_token = auth(agent)["Authorization"].split()[1]
        with client.websocket_connect(f"/api/v1/internal-messages/ws?token={agent_token}") as socket:
            print("EVIDENCE websocket: authenticated agent connected")
            socket.send_json({"type": "send", "thread_id": thread_id, "content": "live hello"})
            event = socket.receive_json()
            print("EVIDENCE websocket live event:", event)
            assert event["type"] == "message" and event["message"]["content"] == "live hello"

        # A foreign account cannot open, send into, or discover the thread.
        assert client.get(f"/api/v1/internal-messages/threads/{thread_id}/messages", headers=auth(outsider)).status_code == 404
        assert client.post(f"/api/v1/internal-messages/threads/{thread_id}/messages", headers=auth(outsider), json={"content": "intrusion"}).status_code == 404
        assert client.get("/api/v1/internal-messages/threads", headers=auth(outsider)).json() == []
        print("EVIDENCE cross-business history/send: 404/404; list: []")

        # Messages during a disconnect remain durable and are recovered from history on reconnect.
        missed = client.post(f"/api/v1/internal-messages/threads/{thread_id}/messages", headers=auth(admin), json={"content": "sent while offline"})
        assert missed.status_code == 201
        history = client.get(f"/api/v1/internal-messages/threads/{thread_id}/messages", headers=auth(agent))
        assert [m["content"] for m in history.json()] == ["live hello", "sent while offline"]
        print("EVIDENCE reconnect catch-up history:", [m["content"] for m in history.json()])
    finally:
        app.dependency_overrides.clear(); db.close(); Base.metadata.drop_all(engine)
