"""
Basic test suite for authentication flows.
Run with: pytest tests/
"""
import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "name": "Test User", "email": "test@vpool.com",
        "phone": "9998887770", "password": "secret123"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@vpool.com"


def test_register_duplicate_email_fails(client):
    payload = {"name": "Test User", "email": "dup@vpool.com", "phone": "9998887771", "password": "secret123"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422
    assert resp.get_json()["success"] is False


def test_register_missing_fields_fails(client):
    resp = client.post("/api/auth/register", json={"name": "No Email"})
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    assert any("email" in e for e in errors)


def test_login_success(client):
    client.post("/api/auth/register", json={
        "name": "Login User", "email": "login@vpool.com", "phone": "9998887772", "password": "secret123"
    })
    resp = client.post("/api/auth/login", json={"email": "login@vpool.com", "password": "secret123"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_login_wrong_password_fails(client):
    client.post("/api/auth/register", json={
        "name": "Login User2", "email": "login2@vpool.com", "phone": "9998887773", "password": "secret123"
    })
    resp = client.post("/api/auth/login", json={"email": "login2@vpool.com", "password": "wrongpass"})
    assert resp.status_code == 422


def test_protected_route_requires_login(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
