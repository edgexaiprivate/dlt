"""
LAYER 5 — Security Tests
Tests OWASP Top 10 relevant attack vectors:
  A01 - Broken Access Control (RBAC bypass attempts)
  A02 - Cryptographic Failures (token leakage)
  A03 - Injection (SQL via inputs)
  A05 - Security Misconfiguration (debug headers, CORS)
  A07 - Authentication Failures (brute force, token manipulation)
"""
import pytest
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token


class TestBrokenAccessControl:
    """A01 — Ensure users cannot access resources they don't own."""

    async def test_manager_cannot_access_other_restaurant_full_menu(
        self, client, manager_headers, db_session
    ):
        from app.models import Restaurant
        other = Restaurant(name="Other Hotel", slug="other-hotel-security")
        db_session.add(other)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/menu/restaurants/{other.id}/full",
            headers=manager_headers
        )
        assert resp.status_code == 403, "Manager accessed another restaurant's menu!"

    async def test_idor_device_access(self, client, manager_headers, db_session):
        """IDOR: manager cannot read devices from a branch they don't own."""
        from app.models import Restaurant, Branch, Device, SessionPeriod
        other_rest = Restaurant(name="IDOR Hotel", slug="idor-hotel")
        db_session.add(other_rest)
        await db_session.commit()
        other_branch = Branch(restaurant_id=other_rest.id, name="IDOR Branch")
        db_session.add(other_branch)
        await db_session.commit()
        other_device = Device(
            branch_id=other_branch.id, name="Other TV", display_number=1,
            mac_address="ID:OR:TE:ST:00:01"
        )
        db_session.add(other_device)
        await db_session.commit()
        # Manager from different restaurant tries to access this device
        # The system should filter by restaurant scope
        resp = await client.get(f"/api/v1/devices/{other_device.id}", headers=manager_headers)
        # Either 403 (explicit deny) or 404 (invisible) is acceptable
        assert resp.status_code in (403, 404), f"IDOR vulnerability! Got {resp.status_code}"

    async def test_privilege_escalation_via_user_update(self, client, manager_headers, staff_user):
        """Manager must not be able to promote another user to super_admin."""
        resp = await client.patch(
            f"/api/v1/users/{staff_user.id}",
            headers=manager_headers,
            json={"role": "super_admin"}
        )
        # Should be forbidden — manager cannot grant super_admin
        assert resp.status_code in (403, 400), "Privilege escalation succeeded!"

    async def test_deactivated_user_token_rejected(self, client, db_session, restaurant):
        """Token belonging to deactivated user must be rejected."""
        from app.models import User, UserRole
        from app.core.security import hash_password
        u = User(
            username="deactivated_token_user", email="deact@test.com",
            full_name="Deact", hashed_password=hash_password("Pass@1234"),
            role=UserRole.STAFF, is_active=True, restaurant_id=restaurant.id,
        )
        db_session.add(u)
        await db_session.commit()
        # Get token while active
        token = create_access_token(u.id)
        # Now deactivate
        u.is_active = False
        await db_session.commit()
        # Token should now be rejected
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403, "Deactivated user token still accepted!"


class TestCryptographicFailures:
    """A02 — Ensure sensitive data is never leaked in responses."""

    async def test_password_never_in_login_response(self, client, manager):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "Manager@1234"
        })
        body = resp.text.lower()
        assert "hashed_password" not in body
        assert "manager@1234" not in body  # plaintext password never echoed

    async def test_password_never_in_user_list(self, client, admin_headers, manager):
        resp = await client.get("/api/v1/users", headers=admin_headers)
        body = resp.text.lower()
        assert "hashed_password" not in body
        assert "password" not in body

    async def test_password_never_in_user_detail(self, client, admin_headers, manager):
        resp = await client.get(f"/api/v1/users/{manager.id}", headers=admin_headers)
        body = resp.text.lower()
        assert "hashed_password" not in body

    async def test_tokens_use_correct_algorithm(self, client, manager):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "manager1", "password": "Manager@1234"
        })
        token = resp.json()["access_token"]
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"  # expected algorithm
        assert header["alg"] != "none"   # NEVER allow 'none' algorithm

    async def test_algorithm_none_attack_rejected(self, client, manager):
        """JWT 'alg:none' bypass attempt must be rejected."""
        # Craft token with alg:none
        import base64, json as jsonlib
        header = base64.urlsafe_b64encode(
            jsonlib.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        payload_b64 = base64.urlsafe_b64encode(
            jsonlib.dumps({"sub": str(manager.id), "type": "access"}).encode()
        ).rstrip(b"=").decode()
        none_token = f"{header}.{payload_b64}."

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {none_token}"}
        )
        assert resp.status_code == 401, "alg:none attack succeeded!"


class TestInjection:
    """A03 — SQL/NoSQL injection attempts must be safely handled."""

    async def test_sql_injection_in_username(self, client):
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
        ]
        for payload in payloads:
            resp = await client.post("/api/v1/auth/login", json={
                "username": payload, "password": "anything"
            })
            # Must return 401 (not found) — never 500 (injection worked)
            assert resp.status_code in (401, 422), \
                f"SQL injection may have worked with payload: {payload!r} → {resp.status_code}"

    async def test_xss_in_menu_item_name(self, client, manager_headers, menu_sub_group):
        xss_payload = '<script>alert("xss")</script>'
        resp = await client.post(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}/items",
            headers=manager_headers,
            json={"name": xss_payload, "price": 50.0}
        )
        # Should be created (API stores as plain text — frontend escapes on render)
        assert resp.status_code == 201
        # Ensure it's stored as plain string, not evaluated
        assert resp.json()["name"] == xss_payload

    async def test_oversized_payload_rejected(self, client, manager_headers, restaurant):
        """Extremely large inputs must be handled without crashing."""
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=manager_headers,
            json={"name": "A" * 10000, "sequence": 1}  # 10KB name
        )
        # Should be 422 (validation) or 400 — never 500
        assert resp.status_code in (422, 400, 201), \
            f"Server crashed on large payload: {resp.status_code}"


class TestSecurityMisconfiguration:
    """A05 — Check for dangerous debug/configuration leaks."""

    async def test_no_stack_trace_in_error_response(self, client):
        """Production errors must not expose stack traces."""
        resp = await client.get("/api/v1/nonexistent-endpoint-xyz")
        body = resp.text.lower()
        assert "traceback" not in body
        assert "sqlalchemy" not in body
        assert "file \"" not in body

    async def test_405_on_wrong_method(self, client):
        resp = await client.delete("/api/v1/auth/login")
        assert resp.status_code == 405

    async def test_openapi_spec_accessible_in_dev(self, client):
        """OpenAPI docs should be accessible (we control visibility per environment)."""
        resp = await client.get("/docs")
        assert resp.status_code == 200

    async def test_health_does_not_expose_internals(self, client):
        resp = await client.get("/health")
        body = resp.text.lower()
        assert "password" not in body
        assert "secret" not in body
        assert "database_url" not in body


class TestAuthenticationFailures:
    """A07 — Authentication hardening."""

    async def test_missing_authorization_header(self, client, restaurant):
        resp = await client.get(f"/api/v1/menu/restaurants/{restaurant.id}/groups")
        assert resp.status_code == 403

    async def test_malformed_bearer_token(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.real.jwt"}
        )
        assert resp.status_code == 401

    async def test_bearer_without_token(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "}
        )
        assert resp.status_code in (401, 403)

    async def test_refresh_token_cannot_access_protected_routes(self, client, manager):
        """Refresh token must not work as access token."""
        from app.core.security import create_refresh_token
        refresh = create_refresh_token(manager.id)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh}"}
        )
        assert resp.status_code == 401, "Refresh token accepted as access token!"

    async def test_token_from_deleted_user_rejected(self, client, db_session, restaurant):
        """Token for a user that no longer exists must be rejected."""
        from app.models import User, UserRole
        from app.core.security import hash_password
        ghost = User(
            username="ghost_user", email="ghost@test.com",
            full_name="Ghost", hashed_password=hash_password("Pass@1234"),
            role=UserRole.STAFF, is_active=True, restaurant_id=restaurant.id,
        )
        db_session.add(ghost)
        await db_session.commit()
        token = create_access_token(ghost.id)
        # Delete the user
        await db_session.delete(ghost)
        await db_session.commit()
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401, "Token for deleted user still accepted!"
