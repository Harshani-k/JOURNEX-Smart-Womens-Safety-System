import time
import pytest
from flask_jwt_extended import create_access_token

def test_successful_registration(client):
    """Verify new user registration returns 201 and valid tokens."""
    payload = {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone_number": "+919876543210",
        "password": "SecurePassword123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "data" in json_data
    assert json_data["data"]["user"]["email"] == "priya.sharma@example.com"
    assert json_data["data"]["user"]["full_name"] == "Priya Sharma"
    assert "password_hash" not in json_data["data"]["user"]
    assert "access_token" in json_data["data"]["tokens"]
    assert "refresh_token" in json_data["data"]["tokens"]

def test_duplicate_email_rejection(client):
    """Verify registration with duplicate email returns 409 Conflict."""
    payload = {
        "full_name": "Ananya Rao",
        "email": "ananya.rao@example.com",
        "phone_number": "+919876543211",
        "password": "SafePass123"
    }
    # First registration succeeds
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email fails
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    data = resp2.get_json()
    assert data["success"] is False
    assert "already exists" in data["message"]

def test_invalid_email_rejection(client):
    """Verify invalid email formats are rejected with 400 Bad Request."""
    invalid_emails = ["not-an-email", "missing-at-domain.com", "user@.com", ""]
    for bad_email in invalid_emails:
        payload = {
            "full_name": "Test User",
            "email": bad_email,
            "phone_number": "+919876543212",
            "password": "Password123"
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

def test_weak_password_rejection(client):
    """Verify passwords failing complexity rules are rejected with 400 Bad Request."""
    weak_passwords = [
        "short1",        # < 8 chars
        "alllettersnohere", # no digit
        "1234567890",    # no letter
        ""               # empty
    ]
    for weak_pw in weak_passwords:
        payload = {
            "full_name": "Test User",
            "email": f"test_{abs(hash(weak_pw))}@example.com",
            "phone_number": "+919876543213",
            "password": weak_pw
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

def test_successful_login(client):
    """Verify registered user can log in and receive valid JWT tokens."""
    reg_payload = {
        "full_name": "Kavita Patel",
        "email": "kavita.patel@example.com",
        "phone_number": "+919876543214",
        "password": "KavitaPassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "kavita.patel@example.com",
        "password": "KavitaPassword123"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]
    assert data["data"]["user"]["email"] == "kavita.patel@example.com"

def test_incorrect_password(client):
    """Verify login with incorrect password returns 401 Unauthorized."""
    reg_payload = {
        "full_name": "Meera Sen",
        "email": "meera.sen@example.com",
        "phone_number": "+919876543215",
        "password": "CorrectPassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "meera.sen@example.com",
        "password": "WrongPassword456"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False
    assert "Invalid email or password" in data["message"]

def test_unknown_user_login(client):
    """Verify login for non-existent user returns 401 Unauthorized."""
    login_payload = {
        "email": "nonexistent.user@example.com",
        "password": "SomePassword123"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False
    assert "Invalid email or password" in data["message"]

def test_access_without_token(client):
    """Verify accessing protected endpoint /me without token returns 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False
    assert data["errors"]["code"] == "AUTHORIZATION_REQUIRED"

def test_access_with_valid_token(client):
    """Verify accessing /me with valid Bearer token returns 200 and profile."""
    reg_payload = {
        "full_name": "Ritu Verma",
        "email": "ritu.verma@example.com",
        "phone_number": "+919876543216",
        "password": "RituPassword123"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.get_json()["data"]["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    data = me_resp.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "ritu.verma@example.com"
    assert data["data"]["full_name"] == "Ritu Verma"

def test_expired_token(client, app):
    """Verify expired token returns 401 with TOKEN_EXPIRED code."""
    from datetime import timedelta
    with app.app_context():
        short_token = create_access_token(identity="1", expires_delta=timedelta(milliseconds=10))

    time.sleep(0.05)

    headers = {"Authorization": f"Bearer {short_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False
    assert data["errors"]["code"] == "TOKEN_EXPIRED"

def test_logout_and_token_revocation(client):
    """Verify token is revoked upon logout and cannot be used subsequently."""
    reg_payload = {
        "full_name": "Sita Devi",
        "email": "sita.devi@example.com",
        "phone_number": "+919876543218",
        "password": "SitaPassword123"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.get_json()["data"]["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    # Initial access succeeds
    resp1 = client.get("/api/v1/auth/me", headers=headers)
    assert resp1.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.get_json()["success"] is True

    # Subsequent access with same token is rejected
    resp2 = client.get("/api/v1/auth/me", headers=headers)
    assert resp2.status_code == 401
    assert resp2.get_json()["errors"]["code"] == "TOKEN_REVOKED"

def test_refresh_token_lifecycle(client):
    """Verify refresh token issues a new valid access token."""
    reg_payload = {
        "full_name": "Geeta Singh",
        "email": "geeta.singh@example.com",
        "phone_number": "+919876543219",
        "password": "GeetaPassword123"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    tokens = reg_resp.get_json()["data"]["tokens"]
    refresh_token = tokens["refresh_token"]

    refresh_headers = {"Authorization": f"Bearer {refresh_token}"}
    refresh_resp = client.post("/api/v1/auth/refresh", headers=refresh_headers)
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.get_json()["data"]["access_token"]
    assert new_token != tokens["access_token"]

    # Use new access token to query /me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_resp.status_code == 200
    assert me_resp.get_json()["data"]["email"] == "geeta.singh@example.com"

def test_user_data_isolation(client):
    """Verify User A's session token cannot be used to retrieve User B's identity."""
    # Register User A
    user_a = {
        "full_name": "User Alpha",
        "email": "alpha@example.com",
        "phone_number": "+919876543201",
        "password": "AlphaPassword123"
    }
    resp_a = client.post("/api/v1/auth/register", json=user_a)
    token_a = resp_a.get_json()["data"]["tokens"]["access_token"]

    # Register User B
    user_b = {
        "full_name": "User Beta",
        "email": "beta@example.com",
        "phone_number": "+919876543202",
        "password": "BetaPassword123"
    }
    resp_b = client.post("/api/v1/auth/register", json=user_b)
    token_b = resp_b.get_json()["data"]["tokens"]["access_token"]

    # Profile check with Token A returns User Alpha
    profile_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}).get_json()
    assert profile_a["data"]["email"] == "alpha@example.com"
    assert profile_a["data"]["full_name"] == "User Alpha"

    # Profile check with Token B returns User Beta
    profile_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"}).get_json()
    assert profile_b["data"]["email"] == "beta@example.com"
    assert profile_b["data"]["full_name"] == "User Beta"

    # Verify ID difference
    assert profile_a["data"]["id"] != profile_b["data"]["id"]

def test_rate_limiting_on_login():
    """Verify that exceeding rate limits on login returns HTTP 429 Too Many Requests."""
    from app import create_app
    from app.extensions import db, limiter
    import app.models

    app = create_app("testing")
    limiter.enabled = True
    client = app.test_client()

    with app.app_context():
        db.create_all()

    # Rate limit on /login is 10 per minute
    for _ in range(10):
        client.post("/api/v1/auth/login", json={"email": "rate@example.com", "password": "WrongPassword123"})

    # 11th request must trigger rate limit
    blocked_resp = client.post("/api/v1/auth/login", json={"email": "rate@example.com", "password": "WrongPassword123"})
    assert blocked_resp.status_code == 429
    data = blocked_resp.get_json()
    assert data["success"] is False
    assert data["errors"]["code"] == 429
    assert "Rate limit exceeded" in data["message"]

    # Reset limiter for subsequent tests
    limiter.enabled = False

