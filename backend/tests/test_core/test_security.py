"""
Tests for security module.

Tests password hashing, JWT token creation and validation.
"""

from datetime import datetime, timedelta

import pytest
from jose import JWTError


def test_password_hashing() -> None:
    """Test that passwords are hashed correctly."""
    from core.security import get_password_hash, verify_password

    plain_password = "mysecretpassword123"
    hashed_password = get_password_hash(plain_password)

    # Hash should be different from plain password
    assert hashed_password != plain_password

    # Should be able to verify the password
    assert verify_password(plain_password, hashed_password) is True


def test_password_verification_fails_with_wrong_password() -> None:
    """Test that password verification fails with wrong password."""
    from core.security import get_password_hash, verify_password

    plain_password = "mysecretpassword123"
    wrong_password = "wrongpassword"
    hashed_password = get_password_hash(plain_password)

    # Wrong password should not verify
    assert verify_password(wrong_password, hashed_password) is False


def test_password_hash_is_different_each_time() -> None:
    """Test that hashing the same password produces different hashes (salt)."""
    from core.security import get_password_hash

    password = "samepassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Different hashes due to salt
    assert hash1 != hash2


def test_create_access_token() -> None:
    """Test JWT access token creation."""
    from core.security import create_access_token

    data = {"sub": "user123", "role": "admin"}
    token = create_access_token(data)

    # Token should be a non-empty string
    assert isinstance(token, str)
    assert len(token) > 0

    # Should have JWT structure (3 parts separated by dots)
    parts = token.split(".")
    assert len(parts) == 3


def test_create_access_token_with_custom_expiration() -> None:
    """Test creating token with custom expiration time."""
    from core.security import create_access_token

    data = {"sub": "user123"}
    expires_delta = timedelta(minutes=15)

    token = create_access_token(data, expires_delta=expires_delta)

    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token() -> None:
    """Test decoding and validating JWT access token."""
    from core.security import create_access_token, decode_access_token

    original_data = {"sub": "user123", "email": "user@example.com"}
    token = create_access_token(original_data)

    # Decode the token
    decoded_data = decode_access_token(token)

    # Should contain the original data
    assert decoded_data["sub"] == original_data["sub"]
    assert decoded_data["email"] == original_data["email"]

    # Should have expiration time
    assert "exp" in decoded_data


def test_decode_invalid_token() -> None:
    """Test that decoding an invalid token raises an error."""
    from core.security import decode_access_token

    invalid_token = "invalid.token.here"

    with pytest.raises(JWTError):
        decode_access_token(invalid_token)


def test_decode_expired_token() -> None:
    """Test that decoding an expired token raises an error."""
    from core.security import create_access_token, decode_access_token

    # Create a token that expires immediately
    data = {"sub": "user123"}
    expires_delta = timedelta(seconds=-1)  # Already expired

    token = create_access_token(data, expires_delta=expires_delta)

    # Should raise error for expired token
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_token_with_missing_claims() -> None:
    """Test that tokens without required claims can still be decoded."""
    from core.security import create_access_token, decode_access_token

    # Create token with minimal data
    data = {}
    token = create_access_token(data)

    # Should be able to decode (even if empty)
    decoded_data = decode_access_token(token)

    # Should still have expiration
    assert "exp" in decoded_data


def test_token_algorithm() -> None:
    """Test that tokens use the configured algorithm."""
    from core.security import create_access_token, decode_access_token
    from jose import jwt

    data = {"sub": "user123"}
    token = create_access_token(data)

    # Decode without verification to inspect header
    from core.config import settings

    unverified = jwt.get_unverified_header(token)

    # Should use configured algorithm
    assert unverified["alg"] == settings.ALGORITHM


def test_verify_password_handles_invalid_hash() -> None:
    """Test that verify_password handles invalid hash gracefully."""
    from core.security import verify_password

    # Invalid hash format should return False, not raise exception
    result = verify_password("password", "invalid_hash")

    assert result is False


def test_password_hash_length() -> None:
    """Test that password hashes have expected length for bcrypt."""
    from core.security import get_password_hash

    password = "testpassword"
    hashed = get_password_hash(password)

    # Bcrypt hashes should be 60 characters
    assert len(hashed) == 60
    # Should start with bcrypt identifier
    assert hashed.startswith("$2b$")
