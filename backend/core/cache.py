"""
Redis caching utilities for performance optimization.

Provides decorators and utilities for caching expensive operations
like analytics aggregations, reducing database load and improving response times.
"""

import hashlib
import json
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis
from loguru import logger

from core.config import settings
from core.constants import CACHE_DEFAULT_TTL


# Global Redis client (initialized lazily)
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client.

    Returns:
        Async Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True
        )

    return _redis_client


def _serialize_value(obj: Any) -> Any:
    """
    Serialize complex types for JSON encoding.

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable representation
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return obj


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key from function name and arguments.

    Args:
        prefix: Cache key prefix (usually function name)
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Serialize arguments to JSON (sorted for consistency)
    try:
        args_str = json.dumps(args, default=_serialize_value, sort_keys=True)
        kwargs_str = json.dumps(kwargs, default=_serialize_value, sort_keys=True)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize cache key arguments: {e}")
        # Fallback to string representation
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))

    # Create hash to keep key length reasonable
    key_data = f"{args_str}:{kwargs_str}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()

    return f"cache:{prefix}:{key_hash}"


def cache_result(ttl: int = CACHE_DEFAULT_TTL, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results in Redis.

    Uses function name and arguments to generate cache key.
    Supports async functions only.

    Args:
        ttl: Time-to-live in seconds (default from constants: 5 minutes)
        key_prefix: Optional custom cache key prefix (defaults to function name)

    Returns:
        Decorator function

    Example:
        @cache_result(ttl=300)
        async def get_analytics_data(start_date, end_date):
            # Expensive database query
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip first arg if it's 'self' (instance method)
            cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args

            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = _make_cache_key(prefix, *cache_args, **kwargs)

            try:
                # Try to get from cache
                redis_client = await get_redis_client()
                cached = await redis_client.get(cache_key)

                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return json.loads(cached)

                logger.debug(f"Cache MISS: {cache_key}")

            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
                # Continue without cache on error

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            try:
                redis_client = await get_redis_client()
                serialized = json.dumps(result, default=_serialize_value)
                await redis_client.setex(cache_key, ttl, serialized)
                logger.debug(f"Cache SET: {cache_key} (TTL={ttl}s)")
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
                # Return result even if caching fails

            return result

        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "cache:analytics:*")

    Returns:
        Number of keys deleted

    Example:
        # Invalidate all analytics caches
        await invalidate_cache_pattern("cache:analytics:*")
    """
    try:
        redis_client = await get_redis_client()

        # Find all matching keys
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache keys matching '{pattern}'")
            return deleted

        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


async def clear_all_cache() -> bool:
    """
    Clear all application cache.

    WARNING: This clears ALL cache keys with 'cache:' prefix.

    Returns:
        True if successful, False otherwise
    """
    try:
        return await invalidate_cache_pattern("cache:*") >= 0
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return False
