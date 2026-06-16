import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_inbox_requires_auth():
    response = client.get("/api/v1/inbox/conversations")
    assert response.status_code == 401

def test_inbox_with_invalid_token():
    response = client.get(
        "/api/v1/inbox/conversations",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
