import uuid

import httpx
import pytest

from app.core.config import settings
from app.services import storage_client
from app.services.storage_client import (
    StorageError,
    create_signed_upload_url,
    upload_image,
)


class _FakeResponse:
    def __init__(self, *, json_data=None, raise_exc: Exception | None = None):
        self._json_data = json_data
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc is not None:
            raise self._raise_exc

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    """httpx.AsyncClient の非同期コンテキストマネージャを模した Fake。"""

    def __init__(
        self,
        *,
        captured: dict,
        json_data=None,
        raise_exc: Exception | None = None,
        **kwargs,
    ):
        captured["client_kwargs"] = kwargs
        self._captured = captured
        self._json_data = json_data
        self._raise_exc = raise_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, *, content=None, json=None, headers):
        self._captured["url"] = url
        self._captured["content"] = content
        self._captured["json"] = json
        self._captured["headers"] = headers
        return _FakeResponse(json_data=self._json_data, raise_exc=self._raise_exc)


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


@pytest.mark.asyncio
async def test_create_signed_upload_url_accepts_supabase_relative_url(monkeypatch):
    _configure(monkeypatch)
    captured: dict = {}
    user_id = uuid.UUID("61bf9d18-48c5-44ec-8b15-fb0b22518c5c")
    storage_path = (
        "clothes/61bf9d18-48c5-44ec-8b15-fb0b22518c5c/"
        "193dfa8e2d30470aa474ebd47d17d765.jpg"
    )
    relative_url = f"/object/upload/sign/clothes-images/{storage_path}?token=test-token"
    monkeypatch.setattr(
        storage_client.uuid,
        "uuid4",
        lambda: uuid.UUID(int=0x193DFA8E2D30470AA474EBD47D17D765),
    )
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(
            captured=captured,
            json_data={"url": relative_url},
            **kw,
        ),
    )

    upload_url, returned_storage_path = await create_signed_upload_url(
        user_id=user_id,
        filename="shirt.jpg",
        content_type="image/jpeg",
    )

    assert returned_storage_path == storage_path
    assert upload_url == f"https://proj.supabase.co/storage/v1{relative_url}"
    assert captured["url"] == (
        "https://proj.supabase.co/storage/v1/object/upload/sign/"
        f"clothes-images/{storage_path}"
    )
    assert captured["json"] == {"upsert": False}
    assert captured["headers"]["Authorization"] == "Bearer service-role-key"


@pytest.mark.asyncio
async def test_create_signed_upload_url_accepts_storage_v1_path(monkeypatch):
    _configure(monkeypatch)
    captured: dict = {}
    user_id = uuid.UUID("61bf9d18-48c5-44ec-8b15-fb0b22518c5c")
    monkeypatch.setattr(storage_client.uuid, "uuid4", lambda: uuid.UUID(int=1))
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(
            captured=captured,
            json_data={
                "signedURL": "/storage/v1/object/upload/sign/clothes-images/clothes/"
                "61bf9d18-48c5-44ec-8b15-fb0b22518c5c/00000000000000000000000000000001.jpg?token=test-token"
            },
            **kw,
        ),
    )

    upload_url, storage_path = await create_signed_upload_url(
        user_id=user_id,
        filename="shirt.jpg",
        content_type="image/jpeg",
    )

    assert storage_path.endswith("00000000000000000000000000000001.jpg")
    assert upload_url.startswith(
        "https://proj.supabase.co/storage/v1/object/upload/sign/"
    )


@pytest.mark.asyncio
async def test_create_signed_upload_url_uses_content_type_extension(monkeypatch):
    _configure(monkeypatch)
    captured: dict = {}
    user_id = uuid.UUID("61bf9d18-48c5-44ec-8b15-fb0b22518c5c")
    monkeypatch.setattr(storage_client.uuid, "uuid4", lambda: uuid.UUID(int=1))
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(
            captured=captured,
            json_data={
                "url": "/object/upload/sign/clothes-images/clothes/"
                "61bf9d18-48c5-44ec-8b15-fb0b22518c5c/00000000000000000000000000000001.jpg?token=test-token"
            },
            **kw,
        ),
    )

    _, storage_path = await create_signed_upload_url(
        user_id=user_id,
        filename="shirt.png",
        content_type="image/jpeg",
    )

    assert storage_path.endswith("00000000000000000000000000000001.jpg")


@pytest.mark.asyncio
async def test_create_signed_upload_url_raises_when_signed_url_missing(monkeypatch):
    _configure(monkeypatch)
    captured: dict = {}
    monkeypatch.setattr(storage_client.uuid, "uuid4", lambda: uuid.UUID(int=1))
    monkeypatch.setattr(
        storage_client.httpx,
        "AsyncClient",
        lambda **kw: _FakeAsyncClient(captured=captured, json_data={}, **kw),
    )

    with pytest.raises(StorageError, match="missing signed URL"):
        await create_signed_upload_url(
            user_id=uuid.UUID("61bf9d18-48c5-44ec-8b15-fb0b22518c5c"),
            filename="shirt.jpg",
            content_type="image/jpeg",
        )
