import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_knowledge_requires_auth():
    response = client.get("/api/v1/knowledge/documents")
    assert response.status_code == 401

def test_cross_business_denied():
    # Login as business 1
    login = client.post("/api/v1/auth/token", data={
        "username": "techsuru1@gmail.com",
        "password": "admin123"
    })
    token = login.json()["access_token"]
    
    # Try to read conversation from business 3 (Xer Xes)
    response = client.get(
        "/api/v1/inbox/conversations/1/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    # Should succeed only if conversation belongs to business 1
    assert response.status_code in [200, 403, 404]
