import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.routers import outfits as outfits_router
from app.api.v1.schemas.outfits import SuggestedOutfit, SuggestedOutfitItem
from app.core.config import settings
from app.domain.outfits.crud import OutfitItemNotOwnedError, _to_outfit_item_schema

TEST_TIMESTAMP = datetime(2026, 6, 4, tzinfo=UTC)
BYPASS_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OWNED_CLOTHES_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")


def _fake_clothes_orm():
    return SimpleNamespace(
        id=OWNED_CLOTHES_ID,
        user_id=BYPASS_USER_ID,
        name="white shirt",
        category="tops",
        color="white",
        pattern=None,
        size="M",
        season=["all"],
        tpo_tags=[SimpleNamespace(tpo_tag="casual")],
        image_url="https://example.com/shirt.jpg",
        thumbnail_url=None,
        memo=None,
        is_favorite=False,
        wear_count=0,
        last_worn_at=None,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


def test_to_outfit_item_schema_owned_uses_db_values() -> None:
    """owned アイテムは手持ち服を解決し、表示フィールドは DB 値で返す。"""
    item = SimpleNamespace(
        clothes=_fake_clothes_orm(),
        role="tops",
        source_type="owned",
        item_snapshot=None,
        display_order=1,
    )

    out = _to_outfit_item_schema(item)

    assert out.clothing_item is not None
    assert out.clothing_item.id == OWNED_CLOTHES_ID
    assert out.name == "white shirt"
    assert out.color == "white"
    assert out.role == "tops"


def test_to_outfit_item_schema_suggested_uses_snapshot() -> None:
    """suggested アイテムは item_snapshot から表示し、clothing_item は None。"""
    item = SimpleNamespace(
        clothes=None,
        role="bottoms",
        source_type="suggested",
        item_snapshot={"name": "提案パンツ", "color": "beige", "pattern": None},
        display_order=2,
    )

    out = _to_outfit_item_schema(item)

    assert out.clothing_item is None
    assert out.name == "提案パンツ"
    assert out.color == "beige"
    assert out.role == "bottoms"


def test_to_outfit_item_schema_owned_deleted_falls_back_to_snapshot() -> None:
    """owned だった服が削除（clothes_id=SET NULL, clothes=None）されても、
    item_snapshot から name/color を表示し続ける（履歴保持）。"""
    item = SimpleNamespace(
        clothes=None,  # 服が削除され clothes_id が SET NULL になった状態
        role="tops",
        source_type="owned",
        item_snapshot={"name": "white shirt", "color": "white", "pattern": None},
        display_order=1,
    )

    out = _to_outfit_item_schema(item)

    assert out.clothing_item is None
    assert out.name == "white shirt"
    assert out.color == "white"
    assert out.role == "tops"


def _saved_outfit(items: list[SuggestedOutfitItem]) -> SuggestedOutfit:
    return SuggestedOutfit(
        id=uuid.UUID("00000000-0000-0000-0000-000000000777"),
        user_id=BYPASS_USER_ID,
        tpo="casual",
        region_code="13_01",
        weather_summary=None,
        comment="c",
        is_favorite=False,
        source="llm",
        items=items,
        created_at=TEST_TIMESTAMP,
    )


def _create_payload() -> dict:
    return {
        "tpo": "casual",
        "region_code": "13_01",
        "weather_summary": "晴れ",
        "weather_temp_max": 27.1,
        "weather_temp_min": 19.8,
        "comment": "c",
        "items": [
            {
                "name": "white shirt",
                "role": "tops",
                "color": "white",
                "pattern": None,
                "display_order": 1,
                "clothes_id": str(OWNED_CLOTHES_ID),
            },
            {
                "name": "提案パンツ",
                "role": "bottoms",
                "color": "beige",
                "pattern": None,
                "display_order": 2,
                "clothes_id": None,
            },
        ],
    }


def test_create_outfit_persists_and_returns_201(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    captured: dict = {}

    async def fake_create_outfit(
        db,
        *,
        user_id,
        tpo,
        region_code,
        comment,
        is_favorite,
        items,
        weather_summary=None,
        weather_temp_max=None,
        weather_temp_min=None,
    ):
        captured["user_id"] = user_id
        captured["region_code"] = region_code
        captured["items"] = items
        captured["weather_summary"] = weather_summary
        captured["weather_temp_max"] = weather_temp_max
        captured["weather_temp_min"] = weather_temp_min
        return _saved_outfit(
            [
                SuggestedOutfitItem(
                    name="white shirt",
                    role="tops",
                    color="white",
                    pattern=None,
                    display_order=1,
                    clothing_item=None,
                ),
            ]
        )

    monkeypatch.setattr(
        outfits_router.outfits_crud, "create_outfit", fake_create_outfit
    )

    response = client.post("/api/v1/outfits", json=_create_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "00000000-0000-0000-0000-000000000777"
    assert body["region_code"] == "13_01"
    # owned/suggested の clothes_id が OutfitCreateItem として渡る
    assert captured["region_code"] == "13_01"
    assert captured["items"][0].clothes_id == OWNED_CLOTHES_ID
    assert captured["items"][1].clothes_id is None
    # 提案時の天気が保存リクエストから crud へ転送される
    assert captured["weather_summary"] == "晴れ"
    assert captured["weather_temp_max"] == 27.1
    assert captured["weather_temp_min"] == 19.8


def test_create_outfit_returns_immediately_and_schedules_image_task(
    client: TestClient, monkeypatch
) -> None:
    """保存 API は画像生成を待たず即時 201 / coordinate_image_url=null を返し、
    画像生成は背景タスクへ保存済みコーデの id / ユーザーで委譲する。"""
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_create_outfit(db, **kwargs):
        return _saved_outfit(
            [
                SuggestedOutfitItem(
                    name="white shirt",
                    role="tops",
                    color="white",
                    pattern=None,
                    display_order=1,
                    clothing_item=None,
                ),
            ]
        )

    captured: dict = {}

    async def fake_background(*, outfit_id, user_id, comment, items):
        captured["outfit_id"] = outfit_id
        captured["user_id"] = user_id
        captured["comment"] = comment
        captured["items"] = items

    monkeypatch.setattr(
        outfits_router.outfits_crud, "create_outfit", fake_create_outfit
    )
    monkeypatch.setattr(
        outfits_router, "generate_and_store_coordinate_image", fake_background
    )

    response = client.post("/api/v1/outfits", json=_create_payload())

    assert response.status_code == 201
    # 画像はまだ生成されていないため応答時点では null
    assert response.json()["coordinate_image_url"] is None
    # 背景タスクが保存済みコーデの id / ユーザーで呼ばれている
    # （TestClient は背景タスクをレスポンス後に同期実行する）
    assert captured["outfit_id"] == uuid.UUID("00000000-0000-0000-0000-000000000777")
    assert captured["user_id"] == BYPASS_USER_ID


def test_create_outfit_rejects_invalid_region(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    payload = _create_payload()
    payload["region_code"] = "99_99"

    response = client.post("/api/v1/outfits", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid region_code"


def test_create_outfit_rejects_not_owned_clothes(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_create_outfit(db, **kwargs):
        raise OutfitItemNotOwnedError({OWNED_CLOTHES_ID})

    monkeypatch.setattr(
        outfits_router.outfits_crud, "create_outfit", fake_create_outfit
    )

    response = client.post("/api/v1/outfits", json=_create_payload())

    assert response.status_code == 400


def test_create_outfit_rejects_empty_items(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    payload = _create_payload()
    payload["items"] = []

    response = client.post("/api/v1/outfits", json=payload)

    assert response.status_code == 422


def test_get_outfit_returns_404_when_missing(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_get_outfit(db, user_id, outfit_id):
        return None

    monkeypatch.setattr(outfits_router.outfits_crud, "get_outfit", fake_get_outfit)

    response = client.get(f"/api/v1/outfits/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_outfit_returns_outfit(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_get_outfit(db, user_id, outfit_id):
        return _saved_outfit([])

    monkeypatch.setattr(outfits_router.outfits_crud, "get_outfit", fake_get_outfit)

    response = client.get("/api/v1/outfits/00000000-0000-0000-0000-000000000777")

    assert response.status_code == 200
    assert response.json()["id"] == "00000000-0000-0000-0000-000000000777"


def test_patch_outfit_toggles_favorite(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    captured: dict = {}

    async def fake_update_outfit(db, user_id, outfit_id, *, is_favorite):
        captured["is_favorite"] = is_favorite
        outfit = _saved_outfit([])
        outfit.is_favorite = is_favorite
        return outfit

    monkeypatch.setattr(
        outfits_router.outfits_crud, "update_outfit", fake_update_outfit
    )

    response = client.patch(
        "/api/v1/outfits/00000000-0000-0000-0000-000000000777",
        json={"is_favorite": True},
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is True
    assert captured["is_favorite"] is True


def test_patch_outfit_returns_404_when_missing(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_update_outfit(db, user_id, outfit_id, *, is_favorite):
        return None

    monkeypatch.setattr(
        outfits_router.outfits_crud, "update_outfit", fake_update_outfit
    )

    response = client.patch(
        f"/api/v1/outfits/{uuid.uuid4()}",
        json={"is_favorite": True},
    )

    assert response.status_code == 404
