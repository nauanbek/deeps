"""
Rate Limiting for External Tools API.

Redis-based rate limiting with sliding window algorithm.
Prevents abuse and ensures fair resource allocation.
"""

import time
from typing import Optional

from fastapi import HTTPException, Request, status
from loguru import logger
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from core.config import settings


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.

    Limits are applied per user for:
    - External tool executions: 60 calls/minute
    - OAuth connections: 10 attempts/hour
    - API requests: 100 requests/minute
    """

    def __init__(self, redis_client: Optional[AsyncRedis] = None):
        """
        Initialize rate limiter.

        Args:
            redis_client: Async Redis client (optional, created if not provided)
        """
        self.redis_client = redis_client
        self._sync_redis: Optional[Redis] = None

    async def _get_redis(self) -> AsyncRedis:
        """Get or create async Redis client."""
        if self.redis_client is None:
            from redis.asyncio import from_url
            self.redis_client = await from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self.redis_client

    def _get_sync_redis(self) -> Redis:
        """Get or create sync Redis client for non-async contexts."""
        if self._sync_redis is None:
            from redis import from_url
            self._sync_redis = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._sync_redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, dict]:
        """
        Check if rate limit is exceeded using sliding window algorithm.

        Args:
            key: Redis key for this rate limit (e.g., "tool_exec:user:123")
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: remaining, reset_at, limit

        Example:
            allowed, info = await limiter.check_rate_limit(
                "tool_exec:user:123",
                limit=60,
                window_seconds=60
            )
            if not allowed:
                raise HTTPException(429, detail="Rate limit exceeded")
        """
        # === SLIDING WINDOW RATE LIMITING ALGORITHM ===
        # This implements a precise sliding window algorithm using Redis sorted sets.
        #
        # How it works:
        # 1. Each request is stored in a Redis sorted set with its timestamp as the score
        # 2. Before checking, we remove all requests older than the current window
        # 3. Count remaining requests in the window
        # 4. If count >= limit, reject; otherwise allow and record new request
        #
        # Why sorted sets?
        # - Scores (timestamps) allow efficient range queries
        # - ZREMRANGEBYSCORE removes old entries in O(log(N)+M) time
        # - ZCARD counts entries in O(1) time
        #
        # Example timeline (60 req/min limit, current time = 100):
        #   Time: [0]--[40]--[45]--[50]--[55]--[100]
        #   Window: [40, 100] (last 60 seconds)
        #   Requests at 40, 45, 50, 55 → count = 4
        #   New request at 100 → count = 5 (allowed if limit >= 5)
        #
        # Advantages over fixed window:
        # - No burst at window boundaries
        # - More accurate rate limiting
        # - Fair distribution of requests
        # === END ALGORITHM DESCRIPTION ===

        redis = await self._get_redis()
        current_time = time.time()

        # Calculate window start time (current_time - window_seconds)
        # Only requests after this time count toward the limit
        window_start = current_time - window_seconds

        # STEP 1: Clean up old requests outside the sliding window
        # Remove all entries with score (timestamp) less than window_start
        # This keeps the sorted set size bounded and maintains accurate counts
        # ZREMRANGEBYSCORE: O(log(N)+M) where M is number removed
        await redis.zremrangebyscore(key, 0, window_start)

        # STEP 2: Count requests currently in the window
        # ZCARD returns the cardinality (count) of the sorted set
        # After cleanup, this is exactly the number of requests in the window
        # ZCARD: O(1) time complexity
        current_count = await redis.zcard(key)

        # STEP 3: Check if limit exceeded
        if current_count >= limit:
            # Rate limit exceeded - reject the request

            # Calculate when the limit will reset (when oldest request expires)
            # Get the oldest entry still in the window (smallest score)
            # ZRANGE: O(log(N)+M) where M=1 (we only get first entry)
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                # Reset time = oldest request time + window duration
                # When the oldest request falls out of the window, limit resets
                reset_at = int(oldest[0][1] + window_seconds)
            else:
                # Edge case: no entries (shouldn't happen but handle gracefully)
                reset_at = int(current_time + window_seconds)

            return False, {
                "remaining": 0,
                "reset_at": reset_at,
                "limit": limit,
                "window_seconds": window_seconds,
            }

        # STEP 4: Limit not exceeded - allow request and record it
        # Add current request to sorted set with timestamp as score
        # Member is string timestamp (must be unique), score is float timestamp
        # ZADD: O(log(N)) time complexity
        await redis.zadd(key, {str(current_time): current_time})

        # STEP 5: Set expiry on the key for automatic cleanup
        # If no requests for 2x window duration, Redis automatically removes the key
        # This prevents memory leaks from abandoned users
        # EXPIRE: O(1) time complexity
        await redis.expire(key, window_seconds * 2)

        # Calculate remaining requests
        # current_count doesn't include the request we just added, so subtract 1 more
        remaining = limit - current_count - 1

        return True, {
            "remaining": remaining,
            "reset_at": int(current_time + window_seconds),
            "limit": limit,
            "window_seconds": window_seconds,
        }

    def check_rate_limit_sync(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, dict]:
        """
        Synchronous version of check_rate_limit.

        For use in synchronous contexts (middleware, decorators).
        """
        redis = self._get_sync_redis()
        current_time = time.time()
        window_start = current_time - window_seconds

        # Remove old entries
        redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_count = redis.zcard(key)

        if current_count >= limit:
            # Rate limit exceeded
            oldest = redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = int(oldest[0][1] + window_seconds)
            else:
                reset_at = int(current_time + window_seconds)

            return False, {
                "remaining": 0,
                "reset_at": reset_at,
                "limit": limit,
                "window_seconds": window_seconds,
            }

        # Add current request
        redis.zadd(key, {str(current_time): current_time})

        # Set expiry
        redis.expire(key, window_seconds * 2)

        remaining = limit - current_count - 1

        return True, {
            "remaining": remaining,
            "reset_at": int(current_time + window_seconds),
            "limit": limit,
            "window_seconds": window_seconds,
        }

    async def check_tool_execution_limit(self, user_id: int) -> tuple[bool, dict]:
        """
        Check rate limit for tool executions.

        Limit: 60 executions per minute per user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        key = f"rate_limit:tool_exec:user:{user_id}"
        return await self.check_rate_limit(key, limit=60, window_seconds=60)

    async def check_oauth_limit(self, user_id: int) -> tuple[bool, dict]:
        """
        Check rate limit for OAuth connection attempts.

        Limit: 10 attempts per hour per user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        key = f"rate_limit:oauth:user:{user_id}"
        return await self.check_rate_limit(key, limit=10, window_seconds=3600)

    async def check_api_limit(self, user_id: int) -> tuple[bool, dict]:
        """
        Check rate limit for general API requests.

        Limit: 100 requests per minute per user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        key = f"rate_limit:api:user:{user_id}"
        return await self.check_rate_limit(key, limit=100, window_seconds=60)


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# Rate Limit Decorators
# ============================================================================


def rate_limit_tool_execution(func):
    """
    Decorator to apply tool execution rate limiting.

    Usage:
        @rate_limit_tool_execution
        async def execute_tool(...):
            ...
    """
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user_id from kwargs or args
        user_id = kwargs.get("user_id")
        if not user_id:
            # Try to find current_user in kwargs
            current_user = kwargs.get("current_user")
            if current_user:
                user_id = current_user.id

        if user_id:
            allowed, info = await rate_limiter.check_tool_execution_limit(user_id)
            if not allowed:
                logger.warning(f"Tool execution rate limit exceeded for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {info['reset_at'] - int(time.time())} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset_at"]),
                    },
                )

        return await func(*args, **kwargs)

    return wrapper


# ============================================================================
# Rate Limit Middleware
# ============================================================================


class RateLimitMiddleware:
    """
    Middleware to apply general API rate limiting.

    Applies 100 requests/minute limit to all authenticated requests
    to /api/v1/external-tools/* endpoints.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Only apply to external-tools endpoints
        if "/external-tools" in request.url.path:
            # Try to get user_id from request state (set by auth dependency)
            user_id = getattr(request.state, "user_id", None)

            if user_id:
                allowed, info = await rate_limiter.check_api_limit(user_id)

                if not allowed:
                    logger.warning(
                        f"API rate limit exceeded for user {user_id} "
                        f"on {request.url.path}"
                    )

                    # Send 429 response
                    from fastapi.responses import JSONResponse

                    response = JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": f"Rate limit exceeded. Try again in {info['reset_at'] - int(time.time())} seconds."
                        },
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(info["reset_at"]),
                        },
                    )
                    await response(scope, receive, send)
                    return

        # Continue to app
        await self.app(scope, receive, send)


# ============================================================================
# Helper Functions
# ============================================================================


def add_rate_limit_headers(response, info: dict):
    """
    Add rate limit headers to response.

    Args:
        response: FastAPI Response object
        info: Rate limit info from check_rate_limit
    """
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset_at"])
    return response
