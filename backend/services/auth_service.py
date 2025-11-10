"""
Authentication service for user management and authentication.

This service handles:
- User registration with validation
- User authentication (login) with account lockout protection
- Password management
- User retrieval operations
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.user import User
from core.security import verify_password, get_password_hash
from schemas.auth import UserRegister
from services.lockout_service import get_lockout_service


class AuthService:
    """Service for authentication and user management operations."""

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession, username: str
    ) -> Optional[User]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username to search for

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(
        db: AsyncSession, email: str
    ) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: Email to search for

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession, user_id: int
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID to search for

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

        Includes account lockout protection:
        - Checks if account is locked before authentication
        - Records failed login attempts
        - Locks account after 5 failed attempts in 10 minutes
        - Auto-unlocks after 15 minutes

        Args:
            db: Database session
            username: Username
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise

        Raises:
            ValueError: If account is locked
        """
        lockout_service = get_lockout_service()

        # Check if account is locked
        if await lockout_service.is_locked(username):
            remaining_time = await lockout_service.get_remaining_lockout_time(username)
            minutes = remaining_time // 60 if remaining_time else 0
            raise ValueError(
                f"Account is temporarily locked due to multiple failed login attempts. "
                f"Please try again in {minutes} minutes."
            )

        # Get user from database
        user = await AuthService.get_user_by_username(db, username)
        if not user:
            # Record failed attempt even for non-existent users (prevents username enumeration timing attacks)
            await lockout_service.record_failed_attempt(username)
            logger.warning(f"Failed login attempt for non-existent user: {username}")
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Record failed attempt
            result = await lockout_service.record_failed_attempt(username)

            if result["locked"]:
                minutes = result["lockout_duration"] // 60
                raise ValueError(
                    f"Account has been locked due to too many failed login attempts. "
                    f"Please try again in {minutes} minutes."
                )

            logger.warning(
                f"Failed login attempt for user '{username}'. "
                f"{result['remaining_attempts']} attempts remaining."
            )
            return None

        # Successful authentication - clear failed attempts
        await lockout_service.record_successful_login(username)
        logger.info(f"Successful login for user '{username}'.")

        return user

    @staticmethod
    async def create_user(
        db: AsyncSession, user_data: UserRegister
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        existing_user = await AuthService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise ValueError("Username already registered")

        # Check if email exists
        existing_email = await AuthService.get_user_by_email(db, user_data.email)
        if existing_email:
            raise ValueError("Email already registered")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    @staticmethod
    async def update_user_password(
        db: AsyncSession, user: User, new_password: str
    ) -> User:
        """
        Update user password.

        Args:
            db: Database session
            user: User to update
            new_password: New plain text password

        Returns:
            Updated user
        """
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_user_email(
        db: AsyncSession, user: User, new_email: str
    ) -> User:
        """
        Update user email.

        Args:
            db: Database session
            user: User to update
            new_email: New email address

        Returns:
            Updated user

        Raises:
            ValueError: If email already exists
        """
        # Check if email is already taken by another user
        existing_user = await AuthService.get_user_by_email(db, new_email)
        if existing_user and existing_user.id != user.id:
            raise ValueError("Email already registered")

        user.email = new_email
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def deactivate_user(
        db: AsyncSession, user: User
    ) -> User:
        """
        Deactivate user account (soft delete).

        Args:
            db: Database session
            user: User to deactivate

        Returns:
            Deactivated user
        """
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def activate_user(
        db: AsyncSession, user: User
    ) -> User:
        """
        Activate user account.

        Args:
            db: Database session
            user: User to activate

        Returns:
            Activated user
        """
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        return user
