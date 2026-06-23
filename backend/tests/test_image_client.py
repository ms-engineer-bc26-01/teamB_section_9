import base64

import pytest
from openai import APIError
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.services.image_client import ImageGenerationError, OpenAIImageClient

_PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-bytes"


def _fake_openai_factory(*, captured: dict, b64: str | None, data_present: bool = True):
    class FakeImages:
        async def generate(self, *, model, prompt, n, size, quality):
            captured["model"] = model
            captured["prompt"] = prompt
            captured["n"] = n
            captured["size"] = size
            captured["quality"] = quality
            if not data_present:
                return type("Resp", (), {"data": []})()
            item = type("ImgData", (), {"b64_json": b64})()
            return type("Resp", (), {"data": [item]})()

    class FakeAsyncOpenAI:
        def __init__(self, *, api_key, timeout=None):
            captured["api_key"] = api_key
            captured["timeout"] = timeout
            self.images = FakeImages()

    return FakeAsyncOpenAI


def test_image_client_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        OpenAIImageClient()


def test_settings_rejects_invalid_openai_image_quality():
    with pytest.raises(ValidationError, match="OPENAI_IMAGE_QUALITY"):
        Settings(
            DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/test",
            OPENAI_IMAGE_QUALITY="fast",
        )


@pytest.mark.asyncio
async def test_generate_image_returns_decoded_bytes(monkeypatch):
    # Arrange
    captured: dict = {}
    b64 = base64.b64encode(_PNG_BYTES).decode("ascii")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_IMAGE_MODEL", "gpt-image-test")
    monkeypatch.setattr(settings, "OPENAI_IMAGE_SIZE", "512x512")
    monkeypatch.setattr(settings, "OPENAI_IMAGE_QUALITY", "low")
    monkeypatch.setattr(
        "app.services.image_client.AsyncOpenAI",
        _fake_openai_factory(captured=captured, b64=b64),
    )

    # Act
    result, usage = await OpenAIImageClient().generate_image(
        "white shirt and black pants"
    )

    # Assert
    assert result == _PNG_BYTES
    # レスポンスに usage が無い場合は None（best-effort）
    assert usage is None
    assert captured["model"] == "gpt-image-test"
    assert captured["size"] == "512x512"
    # 生成時間短縮のため quality 設定が SDK に渡ること
    assert captured["quality"] == "low"
    assert captured["prompt"] == "white shirt and black pants"


@pytest.mark.asyncio
async def test_generate_image_passes_timeout_to_client(monkeypatch):
    # Arrange: 保存APIの長時間ブロックを防ぐため timeout が SDK に渡ること
    captured: dict = {}
    b64 = base64.b64encode(_PNG_BYTES).decode("ascii")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_IMAGE_TIMEOUT_SECONDS", 42.0)
    monkeypatch.setattr(
        "app.services.image_client.AsyncOpenAI",
        _fake_openai_factory(captured=captured, b64=b64),
    )

    # Act
    await OpenAIImageClient().generate_image("prompt")

    # Assert
    assert captured["timeout"] == 42.0


@pytest.mark.asyncio
async def test_generate_image_wraps_api_error(monkeypatch):
    # Arrange
    class FakeImages:
        async def generate(self, **kwargs):
            raise APIError("boom", request=None, body=None)

    class FakeAsyncOpenAI:
        def __init__(self, *, api_key, timeout=None):
            del api_key, timeout
            self.images = FakeImages()

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.image_client.AsyncOpenAI", FakeAsyncOpenAI)

    # Act / Assert
    with pytest.raises(ImageGenerationError) as exc_info:
        await OpenAIImageClient().generate_image("prompt")
    assert isinstance(exc_info.value.__cause__, APIError)


@pytest.mark.asyncio
async def test_generate_image_raises_on_empty_data(monkeypatch):
    # Arrange
    captured: dict = {}
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.image_client.AsyncOpenAI",
        _fake_openai_factory(captured=captured, b64=None, data_present=False),
    )

    # Act / Assert
    with pytest.raises(ImageGenerationError, match="no data"):
        await OpenAIImageClient().generate_image("prompt")


@pytest.mark.asyncio
async def test_generate_image_raises_on_missing_b64(monkeypatch):
    # Arrange
    captured: dict = {}
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.image_client.AsyncOpenAI",
        _fake_openai_factory(captured=captured, b64=None),
    )

    # Act / Assert
    with pytest.raises(ImageGenerationError, match="no image content"):
        await OpenAIImageClient().generate_image("prompt")
