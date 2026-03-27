"""
Tests for /auth/* endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestLogin:
    def test_login_success(self, client: TestClient):
        resp = client.post(
            "/auth/login",
            json={"email": "admin@bank.com", "password": "changeme"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        user = data["user"]
        assert user["email"] == "admin@bank.com"
        assert user["role"] == "ADMIN"
        assert user["is_active"] is True

    def test_login_wrong_password(self, client: TestClient):
        resp = client.post(
            "/auth/login",
            json={"email": "admin@bank.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client: TestClient):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@nowhere.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields(self, client: TestClient):
        resp = client.post("/auth/login", json={"email": "admin@bank.com"})
        assert resp.status_code == 422  # validation error


class TestTokenEndpoint:
    """Swagger UI OAuth2 form-data endpoint."""

    def test_token_success(self, client: TestClient):
        resp = client.post(
            "/auth/token",
            data={"username": "admin@bank.com", "password": "changeme"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_token_wrong_password(self, client: TestClient):
        resp = client.post(
            "/auth/token",
            data={"username": "admin@bank.com", "password": "bad"},
        )
        assert resp.status_code == 401


class TestGetMe:
    def test_get_me_authenticated(self, client: TestClient, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@bank.com"
        assert data["role"] == "ADMIN"
        assert "id" in data

    def test_get_me_no_token(self, client: TestClient):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        resp = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_success(self, client: TestClient, auth_token):
        refresh_token = auth_token["refresh_token"]
        resp = client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        # New access token should be different from the original
        assert data["access_token"] != auth_token["access_token"]

    def test_refresh_with_access_token_rejected(
        self, client: TestClient, auth_token
    ):
        """Passing an access token to /refresh should fail (wrong token type)."""
        resp = client.post(
            "/auth/refresh", json={"refresh_token": auth_token["access_token"]}
        )
        assert resp.status_code == 401

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post(
            "/auth/refresh", json={"refresh_token": "not.a.valid.jwt"}
        )
        assert resp.status_code == 401


class TestLogout:
    def test_logout_returns_success(self, client: TestClient, auth_headers):
        resp = client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_logout_without_auth_still_ok(self, client: TestClient):
        """Stateless JWT — logout is a no-op, no auth required."""
        resp = client.post("/auth/logout")
        assert resp.status_code == 200
