import pytest
from redis.exceptions import RedisError

from app.core import redis as redis_module


def test_get_redis_returns_singleton(monkeypatch) -> None:
    """get_redis は同一クライアントを使い回す。"""
    monkeypatch.setattr(redis_module, "_redis_client", None)
    created: list[object] = []

    class FakeClient:
        pass

    def fake_from_url(url, **kwargs):
        del url, kwargs
        client = FakeClient()
        created.append(client)
        return client

    monkeypatch.setattr(redis_module, "from_url", fake_from_url)

    first = redis_module.get_redis()
    second = redis_module.get_redis()

    assert first is second
    assert len(created) == 1


@pytest.mark.asyncio
async def test_ping_redis_returns_true_on_success(monkeypatch) -> None:
    class FakeClient:
        async def ping(self) -> bool:
            return True

    monkeypatch.setattr(redis_module, "_redis_client", FakeClient())

    assert await redis_module.ping_redis() is True


@pytest.mark.asyncio
async def test_ping_redis_returns_false_on_redis_error(monkeypatch) -> None:
    """接続失敗時は例外を握りつぶして False を返す。"""

    class FakeClient:
        async def ping(self) -> bool:
            raise RedisError("connection refused")

    monkeypatch.setattr(redis_module, "_redis_client", FakeClient())

    assert await redis_module.ping_redis() is False


@pytest.mark.asyncio
async def test_close_redis_resets_client(monkeypatch) -> None:
    closed: list[bool] = []

    class FakeClient:
        async def aclose(self) -> None:
            closed.append(True)

    monkeypatch.setattr(redis_module, "_redis_client", FakeClient())

    await redis_module.close_redis()

    assert closed == [True]
    assert redis_module._redis_client is None
