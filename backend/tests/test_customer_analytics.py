from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from test_analytics import analytics_data, auth_headers, client, params


def test_customer_analytics_access_and_tenant_isolation(analytics_data):
    path = "/api/v1/analytics/customers/summary"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=auth_headers(analytics_data["users"]["agent"])).status_code == 403
    assert client.get(path, headers=auth_headers(analytics_data["users"]["supervisor"]), params=params(analytics_data)).status_code == 200
    assert client.get(path, headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).status_code == 200
    empty = client.get(path, headers=auth_headers(analytics_data["users"]["empty_admin"]), params=params(analytics_data)).json()
    assert empty["metrics"]["active_customers"]["value"] == 0


def test_customer_summary_activity_and_previous_comparison(analytics_data):
    payload = client.get("/api/v1/analytics/customers/summary", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()
    assert payload["metrics"]["active_customers"]["value"] == 2
    assert payload["metrics"]["active_customers"]["previous_value"] == 1
    assert payload["metrics"]["customers_with_open_conversations"]["value"] == 2
    assert any(item["metric"] == "repeat_contact" for item in payload["data_quality"])


def test_active_customer_metrics_search_sort_pagination_and_filters(analytics_data):
    headers = auth_headers(analytics_data["users"]["admin"])
    payload = client.get("/api/v1/analytics/customers/active", headers=headers, params=params(analytics_data, limit=1, sort_by="total_messages")).json()
    assert payload["pagination"]["total"] == 2
    assert len(payload["customers"]) == 1
    customer = payload["customers"][0]
    assert customer["display_name"] == "Facebook Customer"
    assert customer["total_messages"] == 2
    assert customer["customer_messages"] == 1
    assert customer["business_replies"] == 1
    assert customer["active_days"] == 1
    assert customer["currently_open_conversations"] == 1
    assert customer["negative_customer_messages"] == 1
    searched = client.get("/api/v1/analytics/customers/active", headers=headers, params=params(analytics_data, search="Instagram")).json()
    assert searched["pagination"]["total"] == 1
    filtered = client.get("/api/v1/analytics/customers/active", headers=headers, params=params(analytics_data, platform="facebook")).json()
    assert {item["display_name"] for item in filtered["customers"]} == {"Facebook Customer"}


def test_waiting_for_reply_ignores_ai_drafts_and_respects_latest_sent_reply(analytics_data):
    db = SessionLocal(); business_id = analytics_data["ids"]["business"]
    conversation = db.query(Conversation).filter(Conversation.business_id == business_id, Conversation.status == "open").first()
    ai = Message(conversation_id=conversation.id, sender_type="ai", content="Unsent", platform="facebook", timestamp=analytics_data["from"] + __import__("datetime").timedelta(hours=5))
    db.add(ai); db.commit()
    try:
        customers = client.get("/api/v1/analytics/customers/active", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data)).json()["customers"]
        facebook = next(item for item in customers if item["display_name"] == "Facebook Customer")
        assert facebook["waiting_for_reply"] is False
        assert facebook["business_replies"] == 1
    finally:
        db.delete(ai); db.commit(); db.close()


def test_attention_score_components_levels_reasons_and_cap():
    from app.services.analytics_service import AnalyticsService
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    row = {"open_conversations": 8, "pending_conversations": 4, "oldest_unresolved_at": now-timedelta(days=30), "waiting_conversations": 4, "longest_waiting_seconds": 200000, "negative_customer_messages": 10, "classified_customer_messages": 10, "repeat_contact_count": 8, "urgent_conversations": 4, "high_priority_conversations": 4, "last_customer_message_at": now-timedelta(hours=1)}
    score, level, components, reasons = AnalyticsService(None)._attention(row, now)
    assert score == 100
    assert level == "urgent_attention"
    assert all(0 <= component.normalized_value <= 1 for component in components)
    assert reasons


def test_attention_endpoint_is_independent_and_tenant_scoped(analytics_data):
    response = client.get("/api/v1/analytics/customers/attention", headers=auth_headers(analytics_data["users"]["admin"]), params=params(analytics_data))
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] >= 1
    assert all(item["attention_score"] <= 100 for item in payload["customers"])
    assert all("component_breakdown" in item for item in payload["customers"])
    empty = client.get("/api/v1/analytics/customers/attention", headers=auth_headers(analytics_data["users"]["empty_admin"]), params=params(analytics_data)).json()
    assert empty["customers"] == []
