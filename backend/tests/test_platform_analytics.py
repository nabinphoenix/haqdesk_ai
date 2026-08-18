from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.integration import Integration
from app.models.message import Message
from test_analytics import analytics_data, auth_headers, client, params


def by_platform(payload):
    return {item["platform"]: item for item in payload["platforms"]}


def test_platform_access_roles_and_tenant_isolation(analytics_data):
    assert client.get("/api/v1/analytics/platforms").status_code == 401
    assert client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["agent"])).status_code == 403
    supervisor = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["supervisor"]), params=params(analytics_data))
    admin = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data))
    assert supervisor.status_code == admin.status_code == 200
    platforms = by_platform(admin.json())
    assert set(platforms) == {"facebook", "instagram"}
    assert platforms["facebook"]["messages"]["value"] == 2
    assert platforms["instagram"]["messages"]["value"] == 1
    assert all(item["messages"]["value"] < 4 for item in platforms.values())


def test_platform_aggregates_classification_sentiment_response_and_peak(analytics_data):
    response = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data))
    assert response.status_code == 200, response.text
    platforms = by_platform(response.json())
    facebook = platforms["facebook"]
    assert facebook["conversations"]["value"] == 1
    assert facebook["messages"]["value"] == 2
    assert facebook["inbound_messages"]["value"] == 1
    assert facebook["outgoing_messages"]["value"] == 1
    assert facebook["unique_customers"]["value"] == 1
    assert facebook["negative_sentiment_rate"]["value"] == 100
    assert facebook["classified_sentiment_sample_size"] == 1
    assert facebook["positive_messages"]["value"] + facebook["neutral_messages"]["value"] + facebook["negative_messages"]["value"] + facebook["unclassified_messages"]["value"] == facebook["inbound_messages"]["value"]
    assert facebook["unclassified_messages"]["value"] == 0
    assert facebook["median_first_response_seconds"]["value"] == 3600
    assert facebook["p90_first_response_seconds"]["value"] == 3600
    assert facebook["response_sample_size"] == 1
    assert facebook["median_first_response_seconds"]["sample_size"] == 1
    assert facebook["unanswered_conversations"]["value"] == 0
    assert facebook["peak_weekday"] == "thursday"
    assert facebook["peak_hour"] == 3
    instagram = platforms["instagram"]
    assert instagram["outgoing_messages"]["value"] == 0
    assert instagram["unanswered_conversations"]["value"] == 1
    assert instagram["median_first_response_seconds"]["sample_size"] == 0
    assert instagram["median_first_response_seconds"]["value"] is None
    assert instagram["unclassified_messages"]["value"] == 0
    kathmandu = by_platform(client.get(
        "/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, timezone="Asia/Kathmandu"),
    ).json())
    assert kathmandu["facebook"]["peak_hour"] == 8


def test_soft_delete_include_deleted_previous_comparison_and_zero_denominator(analytics_data):
    headers = auth_headers(analytics_data["users"]["admin"])
    base = by_platform(client.get("/api/v1/analytics/platforms", headers=headers, params=params(analytics_data)).json())
    included = by_platform(client.get("/api/v1/analytics/platforms", headers=headers, params=params(analytics_data, include_deleted="true")).json())
    assert base["facebook"]["conversations"]["value"] == 1
    assert included["facebook"]["conversations"]["value"] == 2
    assert included["facebook"]["messages"]["value"] == 3
    assert base["facebook"]["conversations"]["previous_value"] == 1
    assert base["facebook"]["conversations"]["percentage_change"] == 0
    assert base["instagram"]["conversation_share_percentage"]["previous_value"] == 0


def test_connected_historical_email_and_unsupported_whatsapp(analytics_data):
    db = SessionLocal()
    business_id = analytics_data["ids"]["business"]
    records = [
        Integration(business_id=business_id, platform="facebook", access_token="test", status="active"),
        Integration(business_id=business_id, platform="email", access_token="test", status="active"),
        Integration(business_id=business_id, platform="whatsapp", access_token="test", status="active"),
    ]
    db.add_all(records); db.commit()
    try:
        payload = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()
        platforms = by_platform(payload)
        assert platforms["facebook"]["is_connected"] is True
        assert platforms["instagram"]["is_connected"] is False
        assert platforms["email"]["is_connected"] is True
        assert platforms["email"]["conversations"]["value"] == 0
        assert "whatsapp" not in platforms
        assert any(notice["metric"] == "whatsapp_connection" for notice in payload["data_quality"])
    finally:
        for record in records: db.delete(record)
        db.commit(); db.close()


def test_inactive_integration_does_not_activate_a_platform(analytics_data):
    db = SessionLocal()
    record = Integration(business_id=analytics_data["ids"]["business"], platform="email", access_token="test", status="inactive")
    db.add(record); db.commit()
    try:
        payload = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()
        assert "email" not in by_platform(payload)
    finally:
        db.delete(record); db.commit(); db.close()


def test_empty_tenant_and_platform_filter(analytics_data):
    empty = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["empty_admin"]), params=params(analytics_data)).json()
    assert empty["platforms"] == []
    facebook = client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data, platform="facebook")).json()
    assert set(by_platform(facebook)) == {"facebook"}


def test_ai_review_draft_is_not_outgoing_and_unclassified_is_visible(analytics_data):
    db = SessionLocal()
    business_id = analytics_data["ids"]["business"]
    conversation = db.query(Conversation).filter(Conversation.business_id == business_id, Conversation.status == "open").first()
    draft = Message(conversation_id=conversation.id, sender_type="ai", content="Unsent suggestion", platform="facebook", sentiment=None, timestamp=analytics_data["from"] + __import__("datetime").timedelta(hours=5))
    db.add(draft); db.commit()
    try:
        facebook = by_platform(client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json())["facebook"]
        assert facebook["messages"]["value"] == 3
        assert facebook["outgoing_messages"]["value"] == 1
        assert facebook["unclassified_messages"]["value"] == 0
    finally:
        db.delete(draft); db.commit(); db.close()


def test_merged_customer_aliases_are_counted_once(analytics_data):
    db = SessionLocal()
    business_id = analytics_data["ids"]["business"]
    original = db.query(Customer).filter(Customer.business_id == business_id, Customer.platform == "facebook").first()
    master = Customer(business_id=business_id, platform="facebook", platform_user_id="master-platform-test", display_name="Master")
    db.add(master); db.flush()
    original.is_merged = True; original.merged_into_id = master.id
    alias = Customer(business_id=business_id, platform="facebook", platform_user_id="alias-platform-test", display_name="Alias", is_merged=True, merged_into_id=master.id)
    db.add(alias); db.flush()
    conversation = Conversation(business_id=business_id, customer_id=alias.id, status="open", priority="medium", created_at=analytics_data["from"] + __import__("datetime").timedelta(hours=6))
    db.add(conversation); db.commit()
    try:
        facebook = by_platform(client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json())["facebook"]
        assert facebook["conversations"]["value"] == 2
        assert facebook["unique_customers"]["value"] == 1
    finally:
        db.delete(conversation); db.delete(alias)
        original.is_merged = False; original.merged_into_id = None
        db.flush(); db.delete(master); db.commit(); db.close()


def test_platform_trend_is_zero_filled_and_tenant_scoped(analytics_data):
    response = client.get(
        "/api/v1/analytics/platforms/facebook/trend",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data, bucket="day", metric="inbound_messages"),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["platform"] == "facebook"
    assert payload["series"]["total"] == 1
    assert [point["value"] for point in payload["series"]["points"]] == [1, 0, 0]
    assert client.get(
        "/api/v1/analytics/platforms/facebook/trend",
        headers=auth_headers(analytics_data["users"]["agent"]),
        params=params(analytics_data),
    ).status_code == 403
    assert client.get(
        "/api/v1/analytics/platforms/whatsapp/trend",
        headers=auth_headers(analytics_data["users"]["admin"]),
        params=params(analytics_data),
    ).status_code == 422


def test_customer_sentiment_excludes_replies_and_uses_classified_customer_denominator(analytics_data):
    db = SessionLocal()
    business_id = analytics_data["ids"]["business"]
    conversation = db.query(Conversation).filter(Conversation.business_id == business_id, Conversation.status == "open").first()
    timestamp = analytics_data["from"] + __import__("datetime").timedelta(hours=7)
    records = [
        Message(conversation_id=conversation.id, sender_type="customer", content="Unknown mood", platform="facebook", sentiment=None, timestamp=timestamp),
        Message(conversation_id=conversation.id, sender_type="customer", content="Good", platform="facebook", sentiment="positive", timestamp=timestamp),
        Message(conversation_id=conversation.id, sender_type="agent", content="Sent automated reply", platform="facebook", sentiment="negative", timestamp=timestamp),
        Message(conversation_id=conversation.id, sender_type="ai", content="Unsent draft", platform="facebook", sentiment="negative", timestamp=timestamp),
    ]
    db.add_all(records); db.commit()
    try:
        facebook = by_platform(client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json())["facebook"]
        sentiment_total = sum(facebook[key]["value"] for key in ("positive_messages", "neutral_messages", "negative_messages", "unclassified_messages"))
        assert sentiment_total == facebook["inbound_messages"]["value"] == 3
        assert facebook["positive_messages"]["value"] == 1
        assert facebook["negative_messages"]["value"] == 1
        assert facebook["unclassified_messages"]["value"] == 1
        assert facebook["classified_sentiment_sample_size"] == 2
        assert facebook["negative_sentiment_rate"]["value"] == 50
    finally:
        for record in records: db.delete(record)
        db.commit(); db.close()


def test_multiple_answered_conversations_return_response_sample_size(analytics_data):
    db = SessionLocal()
    business_id = analytics_data["ids"]["business"]
    customer = db.query(Customer).filter(Customer.business_id == business_id, Customer.platform == "facebook").first()
    conversation = Conversation(business_id=business_id, customer_id=customer.id, status="open", priority="medium", created_at=analytics_data["from"])
    db.add(conversation); db.flush()
    incoming = Message(conversation_id=conversation.id, sender_type="customer", content="Second question", platform="facebook", timestamp=analytics_data["from"] + __import__("datetime").timedelta(hours=8))
    reply = Message(conversation_id=conversation.id, sender_type="agent", content="Second answer", platform="facebook", timestamp=analytics_data["from"] + __import__("datetime").timedelta(hours=8, minutes=2))
    db.add_all([incoming, reply]); db.commit()
    try:
        facebook = by_platform(client.get("/api/v1/analytics/platforms", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json())["facebook"]
        assert facebook["response_sample_size"] == 2
        assert facebook["median_first_response_seconds"]["sample_size"] == 2
        assert facebook["p90_first_response_seconds"]["sample_size"] == 2
    finally:
        db.delete(reply); db.delete(incoming); db.commit()
        db.delete(conversation); db.commit(); db.close()
