import uuid
from types import SimpleNamespace

import pytest

from app.domain.outfits import image_service
from app.services.image_client import ImageGenerationError
from app.services.storage_client import StorageError

OUTFIT_ID = uuid.UUID("00000000-0000-0000-0000-000000000777")


def _items():
    return [
        SimpleNamespace(
            name="white shirt",
            role="tops",
            color="white",
            pattern=None,
            display_order=1,
        )
    ]


@pytest.mark.asyncio
async def test_generate_coordinate_image_url_success(monkeypatch):
    # Arrange
    captured: dict = {}

    class FakeClient:
        async def generate_image(self, prompt):
            captured["prompt"] = prompt
            return b"png-bytes"

    async def fake_upload(*, path, data, content_type="image/png", upsert=True):
        captured["path"] = path
        captured["data"] = data
        return (
            f"https://proj.supabase.co/storage/v1/object/public/clothes-images/{path}"
        )

    monkeypatch.setattr(image_service, "OpenAIImageClient", lambda: FakeClient())
    monkeypatch.setattr(image_service, "upload_image", fake_upload)

    # Act
    url = await image_service.generate_coordinate_image_url(
        outfit_id=OUTFIT_ID, comment="カジュアル", items=_items()
    )

    # Assert
    assert url.endswith(f"outfits/{OUTFIT_ID}.png")
    assert captured["path"] == f"outfits/{OUTFIT_ID}.png"
    assert captured["data"] == b"png-bytes"
    assert "tops" in captured["prompt"]  # PromptBuilder の出力が渡っている


@pytest.mark.asyncio
async def test_generate_coordinate_image_url_returns_none_on_image_error(monkeypatch):
    # Arrange
    class FakeClient:
        async def generate_image(self, prompt):
            raise ImageGenerationError("api down")

    monkeypatch.setattr(image_service, "OpenAIImageClient", lambda: FakeClient())

    # Act
    url = await image_service.generate_coordinate_image_url(
        outfit_id=OUTFIT_ID, comment="c", items=_items()
    )

    # Assert: best-effort で None
    assert url is None


@pytest.mark.asyncio
async def test_generate_coordinate_image_url_returns_none_on_storage_error(monkeypatch):
    # Arrange
    class FakeClient:
        async def generate_image(self, prompt):
            return b"png-bytes"

    async def fake_upload(**kwargs):
        raise StorageError("upload failed")

    monkeypatch.setattr(image_service, "OpenAIImageClient", lambda: FakeClient())
    monkeypatch.setattr(image_service, "upload_image", fake_upload)

    # Act
    url = await image_service.generate_coordinate_image_url(
        outfit_id=OUTFIT_ID, comment="c", items=_items()
    )

    # Assert
    assert url is None


@pytest.mark.asyncio
async def test_generate_coordinate_image_url_returns_none_when_api_key_missing(
    monkeypatch,
):
    # Arrange: OpenAIImageClient() が ValueError（API キー未設定）を投げる
    def _raise():
        raise ValueError("OPENAI_API_KEY is required for image generation")

    monkeypatch.setattr(image_service, "OpenAIImageClient", _raise)

    # Act
    url = await image_service.generate_coordinate_image_url(
        outfit_id=OUTFIT_ID, comment="c", items=_items()
    )

    # Assert
    assert url is None
