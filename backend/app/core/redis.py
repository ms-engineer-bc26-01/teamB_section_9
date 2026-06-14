"""Async Redis client and connection helpers."""

from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from app.core.config import settings

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
    """Redis が PING に応答すれば True、接続失敗なら False を返す。

    失敗ログはここでは出さず、呼び出し側で用途に応じたレベルで出力する。
    """
    try:
        return await get_redis().ping()
    except RedisError:
        return False


async def close_redis() -> None:
    """Close the shared Redis client (call on application shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
