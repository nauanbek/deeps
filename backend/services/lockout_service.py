"""
Account lockout service for protecting against brute force attacks.

Implements Redis-based account lockout mechanism:
- Tracks failed login attempts
- Locks accounts after threshold reached
- Automatically unlocks after timeout period
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis_async
from loguru import logger

from core.config import settings


class LockoutService:
    """
    Service for managing account lockout to prevent brute force attacks.

    Uses Redis for fast, distributed lockout tracking with automatic expiration.
    """

    # Lockout configuration
    MAX_ATTEMPTS = 5  # Maximum failed login attempts
    LOCKOUT_WINDOW_MINUTES = 10  # Time window for counting attempts
    LOCKOUT_DURATION_MINUTES = 15  # How long account stays locked

    def __init__(self):
        """Initialize Redis connection from settings."""
        self._redis: Optional[redis_async.Redis] = None

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """
        Get or create Redis connection.

        Returns:
            Redis connection instance, or None if Redis unavailable
        """
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,  # 2 second timeout
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                logger.warning(
                    f"Redis connection failed: {e}. "
                    "Account lockout protection disabled."
                )
                return None
        return self._redis

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    def _attempt_key(self, username: str) -> str:
        """Generate Redis key for failed attempts counter."""
        return f"login_attempts:{username}"

    def _lockout_key(self, username: str) -> str:
        """Generate Redis key for lockout flag."""
        return f"account_locked:{username}"

    async def is_locked(self, username: str) -> bool:
        """
        Check if account is currently locked.

        Args:
            username: Username to check

        Returns:
            True if account is locked, False otherwise
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - cannot enforce lockout
            return False

        lockout_key = self._lockout_key(username)

        try:
            is_locked = await redis_client.exists(lockout_key)

            if is_locked:
                # Get remaining lockout time for logging
                ttl = await redis_client.ttl(lockout_key)
                logger.info(
                    f"Account '{username}' is locked. "
                    f"Unlocks in {ttl} seconds."
                )
                return True

            return False
        except Exception as e:
            logger.warning(f"Redis error in is_locked: {e}")
            return False

    async def get_remaining_lockout_time(self, username: str) -> Optional[int]:
        """
        Get remaining lockout time in seconds.

        Args:
            username: Username to check

        Returns:
            Remaining seconds if locked, None if not locked
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - cannot check lockout
            return None

        lockout_key = self._lockout_key(username)

        try:
            if await redis_client.exists(lockout_key):
                ttl = await redis_client.ttl(lockout_key)
                return ttl if ttl > 0 else None

            return None
        except Exception as e:
            logger.warning(f"Redis error in get_remaining_lockout_time: {e}")
            return None

    async def record_failed_attempt(self, username: str) -> dict:
        """
        Record a failed login attempt and check if lockout threshold reached.

        Args:
            username: Username that failed login

        Returns:
            Dictionary with:
                - locked (bool): Whether account is now locked
                - attempts (int): Current number of failed attempts
                - remaining_attempts (int): Attempts until lockout
                - lockout_duration (int): Lockout duration in seconds if locked
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - cannot track attempts
            return {
                "locked": False,
                "attempts": 0,
                "remaining_attempts": self.MAX_ATTEMPTS,
                "lockout_duration": 0,
            }

        attempt_key = self._attempt_key(username)
        lockout_key = self._lockout_key(username)

        try:
            # Increment failed attempts counter
            attempts = await redis_client.incr(attempt_key)

            # Set expiration on first attempt (sliding window)
            if attempts == 1:
                await redis_client.expire(
                    attempt_key,
                    timedelta(minutes=self.LOCKOUT_WINDOW_MINUTES)
                )

            logger.warning(
                f"Failed login attempt for '{username}'. "
                f"Attempt {attempts}/{self.MAX_ATTEMPTS}"
            )

            # Check if lockout threshold reached
            if attempts >= self.MAX_ATTEMPTS:
                # Lock the account
                lockout_duration_seconds = self.LOCKOUT_DURATION_MINUTES * 60
                await redis_client.setex(
                    lockout_key,
                    timedelta(minutes=self.LOCKOUT_DURATION_MINUTES),
                    "locked"
                )

                # Reset attempts counter
                await redis_client.delete(attempt_key)

                logger.error(
                    f"Account '{username}' locked due to {attempts} failed attempts. "
                    f"Locked for {self.LOCKOUT_DURATION_MINUTES} minutes."
                )

                return {
                    "locked": True,
                    "attempts": attempts,
                    "remaining_attempts": 0,
                    "lockout_duration": lockout_duration_seconds,
                }

            return {
                "locked": False,
                "attempts": attempts,
                "remaining_attempts": self.MAX_ATTEMPTS - attempts,
                "lockout_duration": 0,
            }
        except Exception as e:
            logger.warning(f"Redis error in record_failed_attempt: {e}")
            return {
                "locked": False,
                "attempts": 0,
                "remaining_attempts": self.MAX_ATTEMPTS,
                "lockout_duration": 0,
            }

    async def record_successful_login(self, username: str):
        """
        Record successful login and clear failed attempts counter.

        Args:
            username: Username that successfully logged in
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable
            return

        attempt_key = self._attempt_key(username)

        try:
            # Clear failed attempts on successful login
            cleared = await redis_client.delete(attempt_key)

            if cleared:
                logger.info(
                    f"Cleared failed login attempts for '{username}' "
                    f"after successful login."
                )
        except Exception as e:
            logger.warning(f"Redis error in record_successful_login: {e}")

    async def unlock_account(self, username: str) -> bool:
        """
        Manually unlock an account (admin function).

        Args:
            username: Username to unlock

        Returns:
            True if account was locked and unlocked, False if not locked
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - cannot unlock
            return False

        lockout_key = self._lockout_key(username)
        attempt_key = self._attempt_key(username)

        try:
            was_locked = await redis_client.exists(lockout_key)

            if was_locked:
                # Remove lockout and attempts
                await redis_client.delete(lockout_key)
                await redis_client.delete(attempt_key)

                logger.info(f"Manually unlocked account '{username}'.")
                return True

            return False
        except Exception as e:
            logger.warning(f"Redis error in unlock_account: {e}")
            return False

    async def get_lockout_status(self, username: str) -> dict:
        """
        Get detailed lockout status for a user.

        Args:
            username: Username to check

        Returns:
            Dictionary with lockout status information
        """
        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - return default status
            return {
                "locked": False,
                "failed_attempts": 0,
                "remaining_attempts": self.MAX_ATTEMPTS,
                "unlocks_in_seconds": 0,
                "max_attempts": self.MAX_ATTEMPTS,
            }

        attempt_key = self._attempt_key(username)
        lockout_key = self._lockout_key(username)

        try:
            is_locked = await redis_client.exists(lockout_key)
            failed_attempts = await redis_client.get(attempt_key)

            if is_locked:
                lockout_ttl = await redis_client.ttl(lockout_key)
                return {
                    "locked": True,
                    "failed_attempts": 0,
                    "remaining_attempts": 0,
                    "unlocks_in_seconds": lockout_ttl if lockout_ttl > 0 else 0,
                    "max_attempts": self.MAX_ATTEMPTS,
                }

            attempts = int(failed_attempts) if failed_attempts else 0

            return {
                "locked": False,
                "failed_attempts": attempts,
                "remaining_attempts": self.MAX_ATTEMPTS - attempts,
                "unlocks_in_seconds": 0,
                "max_attempts": self.MAX_ATTEMPTS,
            }
        except Exception as e:
            logger.warning(f"Redis error in get_lockout_status: {e}")
            return {
                "locked": False,
                "failed_attempts": 0,
                "remaining_attempts": self.MAX_ATTEMPTS,
                "unlocks_in_seconds": 0,
                "max_attempts": self.MAX_ATTEMPTS,
            }


# Global lockout service instance
_lockout_service: Optional[LockoutService] = None


def get_lockout_service() -> LockoutService:
    """
    Get the global lockout service instance.

    Returns:
        LockoutService instance
    """
    global _lockout_service
    if _lockout_service is None:
        _lockout_service = LockoutService()
    return _lockout_service
