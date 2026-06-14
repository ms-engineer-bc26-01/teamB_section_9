"""Async Redis client and connection helpers."""

import json
from typing import Any

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


async def cache_get_json(key: str) -> dict[str, Any] | None:
    """キャッシュから JSON をデコードして返す。

    ヒット時は dict、ミス時は None。Redis 接続失敗（RedisError）や
    壊れた値（JSON デコード失敗）はキャッシュミス扱いとし、WARNING ログ後 None を返す。
    """
    try:
        raw = await get_redis().get(key)
    except RedisError as exc:
        logger.warning("redis cache get failed (key=%s): %s", key, exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        logger.warning("redis cache value invalid (key=%s): %s", key, exc)
        return None


async def cache_set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    """value を JSON 文字列化して TTL 付きで保存する。

    保存失敗（RedisError）は握りつぶし WARNING ログのみ。
    API レスポンスには影響させない。
    """
    try:
        await get_redis().set(key, json.dumps(value), ex=ttl_seconds)
    except RedisError as exc:
        logger.warning("redis cache set failed (key=%s): %s", key, exc)
