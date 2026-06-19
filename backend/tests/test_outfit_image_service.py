import logging
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
async def test_generate_coordinate_image_url_returns_none_on_storage_error(
    monkeypatch, caplog
):
    # Arrange
    class FakeClient:
        async def generate_image(self, prompt):
            return b"png-bytes"

    async def fake_upload(**kwargs):
        raise StorageError("upload failed")

    monkeypatch.setattr(image_service, "OpenAIImageClient", lambda: FakeClient())
    monkeypatch.setattr(image_service, "upload_image", fake_upload)

    # Act
    with caplog.at_level(logging.WARNING, logger="climo"):
        url = await image_service.generate_coordinate_image_url(
            outfit_id=OUTFIT_ID, comment="c", items=_items()
        )

    # Assert: best-effort で None。失敗フェーズと例外種別が構造化ログに残る
    assert url is None
    assert "phase=storage_upload" in caplog.text
    assert "error=StorageError" in caplog.text


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


USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class _FakeSession:
    """async with SessionLocal() as db: を満たす最小のフェイク。"""

    def __init__(self, store: dict):
        self._store = store

    async def __aenter__(self):
        self._store["db"] = self
        return self

    async def __aexit__(self, *exc):
        return False


@pytest.mark.asyncio
async def test_generate_and_store_saves_url_on_success(monkeypatch):
    """画像生成成功時、独自セッションで set_coordinate_image_url が呼ばれる。"""
    # Arrange
    captured: dict = {}
    image_url = "https://proj.supabase.co/storage/v1/object/public/x/outfits/x.png"

    async def fake_generate(*, outfit_id, comment, items):
        return image_url

    async def fake_set_url(db, user_id, outfit_id, *, coordinate_image_url):
        captured["db"] = db
        captured["user_id"] = user_id
        captured["outfit_id"] = outfit_id
        captured["url"] = coordinate_image_url
        return object()  # 更新成功（対象コーデが見つかった）を表す

    monkeypatch.setattr(image_service, "generate_coordinate_image_url", fake_generate)
    monkeypatch.setattr(image_service, "SessionLocal", lambda: _FakeSession(captured))
    monkeypatch.setattr(image_service, "set_coordinate_image_url", fake_set_url)

    # Act
    await image_service.generate_and_store_coordinate_image(
        outfit_id=OUTFIT_ID, user_id=USER_ID, comment="c", items=_items()
    )

    # Assert: SessionLocal から開いたセッションで保存されている
    assert captured["url"] == image_url
    assert captured["outfit_id"] == OUTFIT_ID
    assert captured["user_id"] == USER_ID
    assert isinstance(captured["db"], _FakeSession)  # SessionLocal から開いたセッション


@pytest.mark.asyncio
async def test_generate_and_store_logs_when_outfit_missing_on_update(
    monkeypatch, caplog
):
    """生成後に対象コーデが見つからない（削除済み等）場合は警告ログを残す。"""
    # Arrange
    store: dict = {}

    async def fake_generate(*, outfit_id, comment, items):
        return "https://proj.supabase.co/storage/v1/object/public/x/outfits/x.png"

    async def fake_set_url(db, user_id, outfit_id, *, coordinate_image_url):
        return None  # 対象が見つからず更新できなかった

    monkeypatch.setattr(image_service, "generate_coordinate_image_url", fake_generate)
    monkeypatch.setattr(image_service, "SessionLocal", lambda: _FakeSession(store))
    monkeypatch.setattr(image_service, "set_coordinate_image_url", fake_set_url)

    # Act
    with caplog.at_level(logging.WARNING, logger="climo"):
        await image_service.generate_and_store_coordinate_image(
            outfit_id=OUTFIT_ID, user_id=USER_ID, comment="c", items=_items()
        )

    # Assert
    assert "outfit not found for update" in caplog.text


@pytest.mark.asyncio
async def test_generate_and_store_skips_save_when_no_image(monkeypatch):
    """画像生成が None のときは set_coordinate_image_url を呼ばない。"""
    # Arrange
    called = {"set_url": False}

    async def fake_generate(*, outfit_id, comment, items):
        return None

    async def fake_set_url(*args, **kwargs):
        called["set_url"] = True

    monkeypatch.setattr(image_service, "generate_coordinate_image_url", fake_generate)
    monkeypatch.setattr(image_service, "set_coordinate_image_url", fake_set_url)

    # Act
    await image_service.generate_and_store_coordinate_image(
        outfit_id=OUTFIT_ID, user_id=USER_ID, comment="c", items=_items()
    )

    # Assert
    assert called["set_url"] is False


@pytest.mark.asyncio
async def test_generate_and_store_swallows_unexpected_errors(monkeypatch, caplog):
    """背景タスクの予期せぬ例外は握りつぶし、ログに残す（リクエストへ波及させない）。"""

    # Arrange
    async def fake_generate(*, outfit_id, comment, items):
        raise RuntimeError("boom")

    monkeypatch.setattr(image_service, "generate_coordinate_image_url", fake_generate)

    # Act / Assert: 例外が伝播しないこと
    with caplog.at_level(logging.WARNING, logger="climo"):
        await image_service.generate_and_store_coordinate_image(
            outfit_id=OUTFIT_ID, user_id=USER_ID, comment="c", items=_items()
        )
    assert "background coordinate image task failed" in caplog.text
