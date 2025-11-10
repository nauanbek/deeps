"""
Security utilities for authentication and authorization.

Provides:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Secure authentication helpers
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # If hash is invalid or verification fails, return False
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> # Token can be used for authentication
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of decoded claims

    Raises:
        JWTError: If token is invalid, expired, or malformed

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> data = decode_access_token(token)
        >>> print(data["sub"])  # "user123"
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    return payload
