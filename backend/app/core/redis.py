"""Async Redis client and connection helpers."""

from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import logger

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Return a lazily-initialized shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def ping_redis() -> bool:
    """Return True if the Redis server responds to PING, False otherwise."""
    try:
        return await get_redis().ping()
    except RedisError as exc:
        logger.error("redis ping failed (url=%s): %s", settings.REDIS_URL, exc)
        return False


async def close_redis() -> None:
    """Close the shared Redis client (call on application shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
