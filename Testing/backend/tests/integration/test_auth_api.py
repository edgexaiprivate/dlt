"""
LAYER 2 — Integration Tests: Auth Endpoints
Tests the full HTTP request/response cycle for /auth/* endpoints.
Uses real DB (SQLite in-memory) and FastAPI test client.

Mandatory cases:
  - Login with valid credentials → 200 + tokens
  - Login with wrong password → 401
  - Login with unknown user → 401
  - Inactive user login → 403
  - Token refresh → new token pair
  - Refresh with access token → 401
  - /auth/me with valid token → user object
  - /auth/me without token → 403
  - /auth/me with expired token → 401
"""
import pytest
from datetime import timedelta
from app.core.security import create_access_token, create_refresh_token


class TestLogin:
    async def test_login_success(self, client, manager):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "Manager@1234"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "manager1"
        assert data["user"]["role"] == "manager"
        # Passwords must NEVER appear in response
        assert "password" not in str(data)
        assert "hashed_password" not in str(data)

    async def test_login_wrong_password(self, client, manager):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "WrongPass"
        })
        assert resp.status_code == 401
        assert "Incorrect" in resp.json()["detail"]

    async def test_login_unknown_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "nobody", "password": "anything"
        })
        assert resp.status_code == 401

    async def test_login_inactive_user(self, client, db_session, restaurant):
        from app.models import User, UserRole
        from app.core.security import hash_password
        u = User(
            username="inactive_user", email="inactive@test.com",
            full_name="Inactive", hashed_password=hash_password("Pass@1234"),
            role=UserRole.STAFF, is_active=False, restaurant_id=restaurant.id,
        )
        db_session.add(u)
        await db_session.commit()

        resp = await client.post("/api/v1/auth/login", json={
            "username": "inactive_user", "password": "Pass@1234"
        })
        assert resp.status_code == 403

    async def test_login_empty_body(self, client):
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422  # Unprocessable Entity

    async def test_login_updates_last_login(self, client, manager, db_session):
        assert manager.last_login is None
        await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "Manager@1234"
        })
        await db_session.refresh(manager)
        assert manager.last_login is not None

    async def test_login_case_sensitive_username(self, client, manager):
        """Username should be case-sensitive."""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "MANAGER1", "password": "Manager@1234"
        })
        assert resp.status_code == 401


class TestTokenRefresh:
    async def test_refresh_returns_new_tokens(self, client, manager):
        login = await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "Manager@1234"
        })
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_access_token_fails(self, client, manager):
        """Must reject access tokens sent to the refresh endpoint."""
        access_token = create_access_token(manager.id)
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401

    async def test_refresh_with_garbage_token_fails(self, client):
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage.token.here"})
        assert resp.status_code == 401

    async def test_refresh_with_expired_token_fails(self, client, manager):
        expired = create_refresh_token.__wrapped__(manager.id) if hasattr(create_refresh_token, "__wrapped__") else None
        # Simulate expired by creating with negative delta
        from jose import jwt
        from datetime import datetime, timezone
        import time
        payload = {"sub": str(manager.id), "type": "refresh",
                   "exp": datetime.now(timezone.utc).timestamp() - 1}
        from app.core.config import settings
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": expired_token})
        assert resp.status_code == 401


class TestGetMe:
    async def test_me_returns_user(self, client, manager, manager_headers):
        resp = await client.get("/api/v1/auth/me", headers=manager_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "manager1"
        assert data["email"] == "manager@test.com"
        assert "hashed_password" not in data

    async def test_me_requires_auth(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403

    async def test_me_with_invalid_token(self, client):
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"})
        assert resp.status_code == 401

    async def test_me_with_expired_token(self, client, manager):
        expired = create_access_token(manager.id, expires_delta=timedelta(seconds=-1))
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401

    async def test_me_reflects_current_user(self, client, super_admin, admin_headers):
        resp = await client.get("/api/v1/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "super_admin"
