"""
Authentication Pydantic schemas for request/response validation.

This module defines all schemas related to user authentication:
- User registration and login
- JWT token handling
- User profile responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from core.password_validator import validate_password


# Token Schemas
class Token(BaseModel):
    """JWT access token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    username: Optional[str] = None
    user_id: Optional[int] = None


# User Authentication Schemas
class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class UserRegister(BaseModel):
    """User registration request."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters, alphanumeric + underscore)"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only allowed characters."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets comprehensive strength requirements.

        Requirements:
        - At least 8 characters long
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - Not a common password

        Raises:
            ValueError: If password doesn't meet requirements
        """
        is_valid, errors = validate_password(v)

        if not is_valid:
            # Join all error messages into a single error
            error_message = "; ".join(errors)
            raise ValueError(error_message)

        return v


# User Response Schemas
class UserResponse(BaseModel):
    """User information response (no sensitive data)."""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """User profile update request."""

    email: Optional[EmailStr] = None

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    """Password change request."""

    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """
        Validate new password meets comprehensive strength requirements.

        Requirements:
        - At least 8 characters long
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - Not a common password

        Raises:
            ValueError: If password doesn't meet requirements
        """
        is_valid, errors = validate_password(v)

        if not is_valid:
            # Join all error messages into a single error
            error_message = "; ".join(errors)
            raise ValueError(error_message)

        return v

    def passwords_match(self) -> bool:
        """Check if new password and confirmation match."""
        return self.new_password == self.confirm_password
