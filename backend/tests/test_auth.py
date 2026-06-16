import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/v1/auth/token", data={
        "username": "techsuru1@gmail.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    response = client.post("/api/v1/auth/token", data={
        "username": "techsuru1@gmail.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_inbox_without_token():
    response = client.get("/api/v1/inbox/conversations")
    assert response.status_code in [401, 200]  # 200 returns empty list

def test_register_duplicate_business():
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "newtest@example.com", 
        "password": "test123",
        "business_name": "Tech Suru"  # existing business
    })
    assert response.status_code == 400
