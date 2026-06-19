import httpx
import pytest

from app.core.config import settings
from app.services import storage_client
from app.services.storage_client import StorageError, upload_image


class _FakeResponse:
    def __init__(self, *, raise_exc: Exception | None = None):
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc is not None:
            raise self._raise_exc


class _FakeAsyncClient:
    """httpx.AsyncClient の非同期コンテキストマネージャを模した Fake。"""

    def __init__(self, *, captured: dict, raise_exc: Exception | None = None, **kwargs):
        captured["client_kwargs"] = kwargs
        self._captured = captured
        self._raise_exc = raise_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, *, content, headers):
        self._captured["url"] = url
        self._captured["content"] = content
        self._captured["headers"] = headers
        return _FakeResponse(raise_exc=self._raise_exc)


def _configure(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "clothes-images")


@pytest.mark.asyncio
async def test_upload_image_returns_public_url_and_uploads(monkeypatch):
    # Arrange
    _configure(monkeypatch)
    captured: dict = {}
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(captured=captured, **kw),
    )

    # Act
    url = await upload_image(path="outfits/abc.png", data=b"img-bytes")

    # Assert
    assert url == (
        "https://proj.supabase.co/storage/v1/object/public/clothes-images/outfits/abc.png"
    )
    assert captured["url"] == (
        "https://proj.supabase.co/storage/v1/object/clothes-images/outfits/abc.png"
    )
    assert captured["content"] == b"img-bytes"
    assert captured["headers"]["Authorization"] == "Bearer service-role-key"
    assert captured["headers"]["Content-Type"] == "image/png"
    assert captured["headers"]["x-upsert"] == "true"


@pytest.mark.asyncio
async def test_upload_image_strips_leading_slash_in_path(monkeypatch):
    # Arrange
    _configure(monkeypatch)
    captured: dict = {}
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(captured=captured, **kw),
    )

    # Act
    url = await upload_image(path="/outfits/abc.png", data=b"x")

    # Assert: 二重スラッシュにならない
    assert "object/clothes-images/outfits/abc.png" in captured["url"]
    assert url.endswith("public/clothes-images/outfits/abc.png")


@pytest.mark.asyncio
async def test_upload_image_raises_when_not_configured(monkeypatch):
    # Arrange
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)

    # Act / Assert
    with pytest.raises(StorageError, match="not configured"):
        await upload_image(path="outfits/abc.png", data=b"x")


@pytest.mark.asyncio
async def test_upload_image_wraps_http_error(monkeypatch):
    # Arrange
    _configure(monkeypatch)
    captured: dict = {}
    http_error = httpx.HTTPError("connection failed")
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(captured=captured, raise_exc=http_error, **kw),
    )

    # Act / Assert
    with pytest.raises(StorageError, match="failed to upload"):
        await upload_image(path="outfits/abc.png", data=b"x")
