"""
LAYER 1 — Unit Tests: Security
Tests password hashing, JWT creation, token decode, edge cases.
No DB, no network. Pure function tests.
"""
import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings


class TestPasswordHashing:
    def test_hash_returns_string(self):
        result = hash_password("Admin@1234")
        assert isinstance(result, str)

    def test_hash_is_not_plaintext(self):
        result = hash_password("Admin@1234")
        assert result != "Admin@1234"

    def test_verify_correct_password(self):
        hashed = hash_password("Admin@1234")
        assert verify_password("Admin@1234", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("Admin@1234")
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_empty_password_fails(self):
        hashed = hash_password("Admin@1234")
        assert verify_password("", hashed) is False

    def test_same_password_produces_different_hashes(self):
        """bcrypt salting — same input must never produce same hash."""
        h1 = hash_password("Admin@1234")
        h2 = hash_password("Admin@1234")
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = hash_password("Admin@1234")
        h2 = hash_password("Admin@1234")
        assert verify_password("Admin@1234", h1) is True
        assert verify_password("Admin@1234", h2) is True

    def test_unicode_password(self):
        pwd = "पासवर्ड@123"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_long_password(self):
        pwd = "A" * 72  # bcrypt max is 72 bytes
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True


class TestAccessToken:
    def test_creates_valid_token(self):
        token = create_access_token(42)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_correct_subject(self):
        token = create_access_token(99)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "99"

    def test_token_type_is_access(self):
        token = create_access_token(1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "access"

    def test_token_has_expiry(self):
        token = create_access_token(1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry(self):
        from datetime import datetime, timezone
        delta = timedelta(hours=2)
        token = create_access_token(1, expires_delta=delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Expiry should be roughly 2 hours from now (within 5 seconds)
        expected = datetime.now(timezone.utc) + delta
        actual_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert abs((actual_exp - expected).total_seconds()) < 5

    def test_subject_as_string_preserved(self):
        token = create_access_token("user-uuid-abc")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user-uuid-abc"


class TestRefreshToken:
    def test_creates_valid_refresh_token(self):
        token = create_refresh_token(1)
        assert isinstance(token, str)

    def test_refresh_type_field(self):
        token = create_refresh_token(1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "refresh"

    def test_access_and_refresh_tokens_differ(self):
        access = create_access_token(1)
        refresh = create_refresh_token(1)
        assert access != refresh


class TestDecodeToken:
    def test_decode_valid_access_token(self):
        token = create_access_token(7)
        payload = decode_token(token)
        assert payload["sub"] == "7"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self):
        token = create_refresh_token(7)
        payload = decode_token(token)
        assert payload["sub"] == "7"
        assert payload["type"] == "refresh"

    def test_tampered_token_raises_401(self):
        token = create_access_token(1)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_empty_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("")
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_401(self):
        bad_token = jwt.encode({"sub": "1", "type": "access"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            decode_token(bad_token)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        token = create_access_token(1, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401
