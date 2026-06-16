import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIError

from app.api.v1.routers import outfits as outfits_router
from app.api.v1.schemas.clothes import ClothingItem
from app.constants.regions import get_region_coordinates
from app.core.config import settings
from app.domain.outfits.service import (
    LLMOutfitSuggestionItem,
    LLMOutfitSuggestionPayload,
    OutfitService,
    OutfitSuggestionError,
)
from app.services.base_llm import LLMStructuredResponseError
from app.services.weather_client import WeatherForecastResponseError

TEST_TIMESTAMP = datetime(2026, 6, 4, tzinfo=UTC)


def _make_forecast(
    *,
    current_temperature: float = 25.4,
    current_weather_code: int = 1,
    current_precipitation_probability: int = 10,
    date: str = "2026-06-04",
    today_temperature_max: float = 27.1,
    today_temperature_min: float = 19.8,
    today_weather_code: int = 1,
    today_precipitation_probability: int = 10,
    cached: bool = False,
) -> dict[str, object]:
    return {
        "current": {
            "temperature_2m": current_temperature,
            "weather_code": current_weather_code,
            "precipitation_probability": current_precipitation_probability,
        },
        "daily": [
            {
                "date": date,
                "temperature_max": today_temperature_max,
                "temperature_min": today_temperature_min,
                "weather_code": today_weather_code,
                "precipitation_probability_max": today_precipitation_probability,
            }
        ],
        "cached": cached,
    }


def _make_prompt_weather(
    *,
    current_temperature: float = 25.0,
    current_weather: str = "晴れ",
    today_weather: str = "晴れ",
    today_temperature_max: float = 27.0,
    today_temperature_min: float = 19.0,
    today_precipitation_probability: int = 10,
) -> dict[str, object]:
    return {
        "current_temperature": current_temperature,
        "current_weather": current_weather,
        "today_weather": today_weather,
        "today_temperature_max": today_temperature_max,
        "today_temperature_min": today_temperature_min,
        "today_precipitation_probability": today_precipitation_probability,
    }


@pytest.mark.asyncio
async def test_outfit_service_uses_prompt_template_independent_of_cwd(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            captured["prompt"] = prompt
            assert response_format is LLMOutfitSuggestionPayload
            return LLMOutfitSuggestionPayload(
                comment="generated-coordinate",
                items=[
                    LLMOutfitSuggestionItem(
                        name="white shirt",
                        role="tops",
                        color="white",
                        pattern=None,
                        clothes_id="00000000-0000-0000-0000-000000000010",
                    )
                ],
            )

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )
    monkeypatch.chdir(tmp_path)

    service = OutfitService()
    result = await service.suggest(
        tpo="casual",
        clothes=[
            ClothingItem(
                id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="white shirt",
                category="tops",
                color="white",
                pattern=None,
                size="M",
                season=["spring", "summer"],
                tpo_tags=["casual"],
                image_url="https://example.com/shirt.jpg",
                thumbnail_url=None,
                memo=None,
                is_favorite=False,
                wear_count=0,
                last_worn_at=None,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            )
        ],
        weather={
            "current_temperature": 25.0,
            "current_weather": "晴れ",
            "today_weather": "晴れ",
            "today_temperature_max": 27.0,
            "today_temperature_min": 19.0,
            "today_precipitation_probability": 10,
        },
    )

    assert result.comment == "generated-coordinate"
    assert "casual" in captured["prompt"]
    assert "id=00000000-0000-0000-0000-000000000010" in captured["prompt"]
    assert "tops - white shirt - color=white" in captured["prompt"]
    assert "現在の気温: 25.0C" in captured["prompt"]
    assert "現在の天気: 晴れ" in captured["prompt"]
    assert "今日の降水確率: 10%" in captured["prompt"]
    assert [item.role for item in result.items] == ["tops"]
    # clothes_id が手持ちに一致するので clothing_item が解決される
    assert result.items[0].clothing_item is not None
    assert result.items[0].clothing_item.name == "white shirt"


@pytest.mark.asyncio
async def test_suggest_resolves_id_prefixed_clothes_id_and_prefers_db_values(
    monkeypatch,
) -> None:
    """clothes_id に id= 接頭辞/空白が混ざっても解決し、手持ちは DB 値を返す。"""
    owned = ClothingItem(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="DBシャツ",
        category="tops",
        color="navy",
        pattern="stripe",
        size="M",
        season=["all"],
        tpo_tags=["casual"],
        image_url="https://example.com/db.jpg",
        thumbnail_url=None,
        memo=None,
        is_favorite=False,
        wear_count=0,
        last_worn_at=None,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            del prompt, response_format
            return LLMOutfitSuggestionPayload(
                comment="c",
                items=[
                    LLMOutfitSuggestionItem(
                        name="LLMが言う名前",
                        role="tops",
                        color="red",
                        pattern=None,
                        # プロンプト提示の "id=<uuid>" 形式 + 末尾空白を模す
                        clothes_id="id=00000000-0000-0000-0000-0000000000aa ",
                    )
                ],
            )

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )
    service = OutfitService()
    result = await service.suggest(
        tpo="casual", clothes=[owned], weather=_make_prompt_weather()
    )

    item = result.items[0]
    assert item.clothing_item is not None
    assert item.clothing_item.id == owned.id
    # 手持ち服は DB 値が正（LLM の食い違う name/color は採用しない）
    assert item.name == "DBシャツ"
    assert item.color == "navy"
    assert item.pattern == "stripe"


@pytest.mark.asyncio
async def test_suggest_returns_null_clothing_item_for_unowned(monkeypatch) -> None:
    """clothes_id=None / 手持ちに無い ID は補完提案として clothing_item=None で返す。"""

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            del prompt, response_format
            return LLMOutfitSuggestionPayload(
                comment="c",
                items=[
                    LLMOutfitSuggestionItem(
                        name="提案ボトム",
                        role="bottoms",
                        color="beige",
                        pattern=None,
                        clothes_id=None,
                    ),
                    LLMOutfitSuggestionItem(
                        name="存在しない服",
                        role="shoes",
                        color=None,
                        pattern=None,
                        clothes_id="99999999-9999-9999-9999-999999999999",
                    ),
                ],
            )

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )
    service = OutfitService()
    result = await service.suggest(
        tpo="casual", clothes=[], weather=_make_prompt_weather()
    )

    assert len(result.items) == 2
    # clothes_id=None → 補完
    assert result.items[0].clothing_item is None
    assert result.items[0].name == "提案ボトム"
    assert result.items[0].color == "beige"
    # 手持ちに無い ID → 補完
    assert result.items[1].clothing_item is None
    assert result.items[1].name == "存在しない服"


def test_suggest_outfit_builds_prompt_from_weather_and_user_clothes(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    resolved_user_id = uuid.UUID("00000000-0000-0000-0000-000000000123")

    async def fake_verify_supabase_jwt(token: str) -> dict[str, object]:
        assert token == "supabase-test-token"
        return {
            "sub": str(resolved_user_id),
            "email": "jwt-user@example.com",
        }

    async def fake_get_or_create_user(db, *, user_id, email):
        assert user_id == resolved_user_id
        assert email == "jwt-user@example.com"
        return type(
            "User",
            (),
            {
                "id": user_id,
                "email": email,
                "default_region_code": "13_01",
            },
        )()

    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        assert latitude == 35.6895
        assert longitude == 139.6917
        assert days == 3
        return _make_forecast()

    async def fake_list_clothes(db, user_id, **kwargs):
        assert user_id == resolved_user_id
        return type(
            "ClothesListResponse",
            (),
            {
                "items": [
                    ClothingItem(
                        id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                        user_id=resolved_user_id,
                        name="white shirt",
                        category="tops",
                        color="white",
                        pattern=None,
                        size="M",
                        season=["spring", "summer"],
                        tpo_tags=["casual"],
                        image_url="https://example.com/shirt.jpg",
                        thumbnail_url=None,
                        memo=None,
                        is_favorite=False,
                        wear_count=0,
                        last_worn_at=None,
                        created_at=TEST_TIMESTAMP,
                        updated_at=TEST_TIMESTAMP,
                    )
                ]
            },
        )()

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            assert "casual" in prompt
            assert "現在の気温: 25.4C" in prompt
            assert "現在の天気: 晴れ" in prompt
            assert "今日の天気: 晴れ" in prompt
            assert "今日の最高気温: 27.1C" in prompt
            assert "今日の最低気温: 19.8C" in prompt
            assert "今日の降水確率: 10%" in prompt
            assert "tops - white shirt - color=white" in prompt
            assert response_format is LLMOutfitSuggestionPayload
            return LLMOutfitSuggestionPayload(
                comment="generated-coordinate",
                items=[
                    LLMOutfitSuggestionItem(
                        name="white shirt",
                        role="tops",
                        color="white",
                        pattern=None,
                        clothes_id="00000000-0000-0000-0000-000000000010",
                    )
                ],
            )

    monkeypatch.setattr(
        "app.dependencies.auth.verify_supabase_jwt", fake_verify_supabase_jwt
    )
    monkeypatch.setattr(
        "app.dependencies.auth.user_crud.get_or_create_user", fake_get_or_create_user
    )
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)
    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        headers={"Authorization": "Bearer supabase-test-token"},
        json={
            "tpo": "casual",
            "date": "2026-06-04",
        },
    )

    assert response.status_code == 200
    body = response.json()
    # 提案レスポンスは outfits のみ（weather_summary / region_used / cached は持たない）
    assert set(body.keys()) == {"outfits"}
    assert len(body["outfits"]) == 1

    outfit = body["outfits"][0]
    # id / created_at は無保存のため一時生成。形式のみ確認し値は固定しない。
    assert uuid.UUID(outfit["id"])
    assert outfit["created_at"]
    assert outfit["user_id"] == str(resolved_user_id)
    assert outfit["tpo"] == "casual"
    assert outfit["comment"] == "generated-coordinate"
    assert outfit["is_favorite"] is False
    assert outfit["items"] == [
        {
            "name": "white shirt",
            "role": "tops",
            "color": "white",
            "pattern": None,
            "display_order": 1,
            "clothing_item": {
                "id": "00000000-0000-0000-0000-000000000010",
                "user_id": str(resolved_user_id),
                "name": "white shirt",
                "category": "tops",
                "color": "white",
                "pattern": None,
                "size": "M",
                "season": ["spring", "summer"],
                "tpo_tags": ["casual"],
                "image_url": "https://example.com/shirt.jpg",
                "thumbnail_url": None,
                "memo": None,
                "is_favorite": False,
                "wear_count": 0,
                "last_worn_at": None,
                "created_at": "2026-06-04T00:00:00Z",
                "updated_at": "2026-06-04T00:00:00Z",
            },
        }
    ]


def test_suggest_outfit_uses_fallback_region_when_user_default_missing(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    resolved_user_id = uuid.UUID("00000000-0000-0000-0000-000000000123")

    async def fake_verify_supabase_jwt(token: str) -> dict[str, object]:
        return {
            "sub": str(resolved_user_id),
            "email": "jwt-user@example.com",
        }

    async def fake_get_or_create_user(db, *, user_id, email):
        return type(
            "User",
            (),
            {
                "id": user_id,
                "email": email,
                "default_region_code": None,
            },
        )()

    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        expected_coordinates = get_region_coordinates("13_01")
        assert expected_coordinates is not None
        assert (latitude, longitude) == expected_coordinates
        return _make_forecast(
            current_temperature=20.0,
            current_weather_code=2,
            current_precipitation_probability=20,
            today_temperature_max=23.0,
            today_temperature_min=18.0,
            today_weather_code=3,
            today_precipitation_probability=20,
        )

    async def fake_list_clothes(db, user_id, **kwargs):
        return type("ClothesListResponse", (), {"items": []})()

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            assert "服の登録はありません。" in prompt
            assert response_format is LLMOutfitSuggestionPayload
            return LLMOutfitSuggestionPayload(comment="generated-coordinate", items=[])

    monkeypatch.setattr(
        "app.dependencies.auth.verify_supabase_jwt", fake_verify_supabase_jwt
    )
    monkeypatch.setattr(
        "app.dependencies.auth.user_crud.get_or_create_user", fake_get_or_create_user
    )
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)
    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        headers={"Authorization": "Bearer supabase-test-token"},
        json={"tpo": "casual"},
    )

    # フォールバック region(13_01) が使われたことは fake_fetch_weather_forecast 内の
    # 座標アサーションで検証済み（response からは region_used を返さない）。
    assert response.status_code == 200
    assert response.json()["outfits"][0]["items"] == []
    assert response.json()["outfits"][0]["comment"] == "generated-coordinate"


@pytest.mark.parametrize(
    "payload",
    [
        {"tpo": "casual", "clothing_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]},
        {
            "tpo": "casual",
            "exclude_clothing_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        },
    ],
)
def test_suggest_outfit_accepts_clothing_filters(
    client: TestClient,
    monkeypatch,
    payload: dict[str, object],
) -> None:
    """clothing_ids / exclude は 400 拒否されず後続へ進む (Issue #61)"""
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        raise WeatherForecastResponseError("invalid weather forecast response")

    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )

    response = client.post("/api/v1/outfits/suggest", json=payload)

    # 400 で弾かれず、weather 取得段階（502）まで到達することを確認
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_suggest_outfit_passes_must_include_ids_to_prompt(monkeypatch) -> None:
    """clothing_ids 指定時は必ず含める服として id 付きでプロンプトに渡す (Issue #61)"""
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            captured["prompt"] = prompt
            assert response_format is LLMOutfitSuggestionPayload
            return LLMOutfitSuggestionPayload(comment="generated-coordinate", items=[])

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    tops_a = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000a1", "tops A", "tops", ["casual"]
    )
    tops_b = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000a2", "tops B", "tops", ["casual"]
    )

    service = OutfitService()
    await service.suggest(
        tpo="casual",
        clothes=[tops_a, tops_b],
        weather=_make_prompt_weather(),
        clothing_ids=[tops_b.id],
    )

    # 必ず含める服セクションに tops_b が id 付きで列挙される
    assert f"- id={tops_b.id} - tops B" in captured["prompt"]


@pytest.mark.asyncio
async def test_suggest_outfit_excludes_specified_clothing_ids_from_prompt(
    monkeypatch,
) -> None:
    """exclude_clothing_ids 指定時はその服をプロンプト候補から除外する (Issue #61)"""
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            captured["prompt"] = prompt
            assert response_format is LLMOutfitSuggestionPayload
            return LLMOutfitSuggestionPayload(comment="generated-coordinate", items=[])

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    tops_keep = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000b1", "keep tops", "tops", ["casual"]
    )
    tops_drop = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000b2",
        "drop tops",
        "tops",
        ["casual"],
        is_favorite=True,
    )

    service = OutfitService()
    await service.suggest(
        tpo="casual",
        clothes=[tops_keep, tops_drop],
        weather=_make_prompt_weather(),
        exclude_clothing_ids=[tops_drop.id],
    )

    # 除外された服はプロンプトに載らず、残した服は載る
    assert "drop tops" not in captured["prompt"]
    assert "keep tops" in captured["prompt"]


def test_select_clothes_includes_all_specified_same_category() -> None:
    """clothing_ids に同カテゴリ複数を指定したら全て含める (Issue #61)"""
    tops_a = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c1", "tops A", "tops", ["casual"]
    )
    tops_b = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c2", "tops B", "tops", ["casual"]
    )

    result = OutfitService._select_clothes(
        tpo="casual",
        clothes=[tops_a, tops_b],
        clothing_ids=[tops_a.id, tops_b.id],
    )

    names = {s.clothing_item.name for s in result}
    assert names == {"tops A", "tops B"}
    assert [s.role for s in result] == ["tops", "tops"]


def test_select_clothes_includes_specified_onepiece_and_tops_together() -> None:
    """onepiece と tops を同時指定したら両方含める（排他より指定を優先）(Issue #61)"""
    onepiece = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c3", "floral onepiece", "onepiece", ["date"]
    )
    tops = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c4", "white tops", "tops", ["date"]
    )

    result = OutfitService._select_clothes(
        tpo="date",
        clothes=[onepiece, tops],
        clothing_ids=[onepiece.id, tops.id],
    )

    names = {s.clothing_item.name for s in result}
    assert names == {"floral onepiece", "white tops"}


def test_select_clothes_autocompletes_unspecified_slots() -> None:
    """指定で埋まらないカテゴリは手持ちから自動補完する (Issue #61)"""
    forced_tops = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c5", "my tops", "tops", ["casual"]
    )
    auto_bottoms = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c6", "auto bottoms", "bottoms", ["casual"]
    )

    result = OutfitService._select_clothes(
        tpo="casual",
        clothes=[forced_tops, auto_bottoms],
        clothing_ids=[forced_tops.id],
    )

    names = {s.clothing_item.name for s in result}
    roles = {s.role for s in result}
    assert names == {"my tops", "auto bottoms"}
    assert roles == {"tops", "bottoms"}


def test_select_clothes_keeps_forced_tops_even_with_favorite_onepiece() -> None:
    """高スコアの onepiece があっても指定した tops は必ず残る (Issue #61 退行防止)"""
    forced_tops = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c7", "forced tops", "tops", ["casual"]
    )
    fav_onepiece = _make_clothing_item(
        "00000000-0000-0000-0000-0000000000c8",
        "fav onepiece",
        "onepiece",
        ["casual"],
        is_favorite=True,
    )

    result = OutfitService._select_clothes(
        tpo="casual",
        clothes=[forced_tops, fav_onepiece],
        clothing_ids=[forced_tops.id],
    )

    names = {s.clothing_item.name for s in result}
    assert "forced tops" in names
    assert "fav onepiece" not in names


@pytest.mark.asyncio
async def test_outfit_service_wraps_llm_api_errors(monkeypatch) -> None:
    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            del prompt
            del response_format
            raise APIError(
                "upstream failure",
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                body=None,
            )

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    service = OutfitService()

    with pytest.raises(OutfitSuggestionError) as exc_info:
        await service.suggest(
            tpo="casual",
            clothes=[],
            weather=_make_prompt_weather(),
        )

    assert str(exc_info.value) == "failed to generate outfit suggestion"
    assert isinstance(exc_info.value.__cause__, APIError)


@pytest.mark.asyncio
async def test_outfit_service_wraps_structured_output_errors(monkeypatch) -> None:
    class FakeLLMClient:
        async def generate_structured(self, prompt: str, *, response_format):
            del prompt
            del response_format
            raise LLMStructuredResponseError("cannot comply")

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    service = OutfitService()

    with pytest.raises(OutfitSuggestionError) as exc_info:
        await service.suggest(
            tpo="casual",
            clothes=[],
            weather=_make_prompt_weather(),
        )

    assert str(exc_info.value) == "failed to generate outfit suggestion"
    assert isinstance(exc_info.value.__cause__, LLMStructuredResponseError)


def test_suggest_outfit_requires_authentication(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_suggest_outfit_returns_bad_gateway_on_llm_failure(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeOutfitService:
        async def suggest(
            self,
            *,
            tpo: str,
            clothes: list[ClothingItem],
            weather: dict,
            clothing_ids=None,
            exclude_clothing_ids=None,
        ) -> str:
            del tpo, clothes, weather, clothing_ids, exclude_clothing_ids
            raise OutfitSuggestionError("failed to generate outfit suggestion")

    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        return _make_forecast(
            current_temperature=25.0,
            today_temperature_max=27.0,
            today_temperature_min=19.0,
        )

    async def fake_list_clothes(db, user_id, **kwargs):
        del db, user_id, kwargs
        return type("ClothesListResponse", (), {"items": []})()

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr("app.api.v1.routers.outfits.OutfitService", FakeOutfitService)
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to generate outfit suggestion"


def test_suggest_outfit_returns_bad_gateway_on_service_initialization_failure(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeOutfitService:
        def __init__(self) -> None:
            raise OutfitSuggestionError("failed to generate outfit suggestion")

    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        return _make_forecast(
            current_temperature=25.0,
            today_temperature_max=27.0,
            today_temperature_min=19.0,
        )

    async def fake_list_clothes(db, user_id, **kwargs):
        del db, user_id, kwargs
        return type("ClothesListResponse", (), {"items": []})()

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr("app.api.v1.routers.outfits.OutfitService", FakeOutfitService)
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to generate outfit suggestion"


def test_suggest_outfit_returns_bad_gateway_on_weather_parse_error(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_fetch_weather_forecast(
        *, region_code: str, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        raise WeatherForecastResponseError("invalid weather forecast response")

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to fetch weather forecast"


def test_select_clothes_tops_wins_over_onepiece_on_equal_score() -> None:
    """同スコアのとき _select_clothes は tops を onepiece より優先する (Issue #60)"""
    tops_item = _make_clothing_item(
        "00000000-0000-0000-0000-000000000010", "white shirt", "tops", ["casual"]
    )
    onepiece_item = _make_clothing_item(
        "00000000-0000-0000-0000-000000000020",
        "floral onepiece",
        "onepiece",
        ["casual"],
    )

    result = OutfitService._select_clothes(
        tpo="casual", clothes=[tops_item, onepiece_item]
    )

    roles = {s.role for s in result}
    names = [s.clothing_item.name for s in result]
    assert "tops" in roles
    assert "onepiece" not in roles
    assert "white shirt" in names
    assert "floral onepiece" not in names


def test_onepiece_selected_when_strictly_higher_score() -> None:
    """onepiece が tops を厳密に上回るスコアのとき onepiece が選ばれる (Issue #60)"""
    tops = _make_clothing_item(
        "00000000-0000-0000-0000-000000000060",
        "plain tops",
        "tops",
        ["casual"],
        is_favorite=False,
    )
    onepiece = _make_clothing_item(
        "00000000-0000-0000-0000-000000000061",
        "favorite onepiece",
        "onepiece",
        ["casual"],
        is_favorite=True,
    )

    result = OutfitService._select_clothes(tpo="casual", clothes=[tops, onepiece])

    roles = {s.role for s in result}
    names = [s.clothing_item.name for s in result]
    assert "onepiece" in roles
    assert "tops" not in roles
    assert "favorite onepiece" in names


def _make_clothing_item(
    uid: str,
    name: str,
    category: str,
    tpo_tags: list[str],
    is_favorite: bool = False,
) -> ClothingItem:
    return ClothingItem(
        id=uuid.UUID(uid),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name=name,
        category=category,
        color=None,
        pattern=None,
        size=None,
        season=["spring"],
        tpo_tags=tpo_tags,
        image_url="https://example.com/img.jpg",
        thumbnail_url=None,
        memo=None,
        is_favorite=is_favorite,
        wear_count=0,
        last_worn_at=None,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


def test_tops_bottoms_win_when_higher_score() -> None:
    """tops/bottoms が is_favorite=True でスコア優位なら onepiece より優先される"""
    tops = _make_clothing_item(
        "00000000-0000-0000-0000-000000000030",
        "favorite tops",
        "tops",
        ["casual"],
        is_favorite=True,
    )
    bottoms = _make_clothing_item(
        "00000000-0000-0000-0000-000000000031",
        "favorite bottoms",
        "bottoms",
        ["casual"],
        is_favorite=True,
    )
    onepiece = _make_clothing_item(
        "00000000-0000-0000-0000-000000000032",
        "plain onepiece",
        "onepiece",
        ["casual"],
    )

    result = OutfitService._select_clothes(
        tpo="casual", clothes=[tops, bottoms, onepiece]
    )

    roles = {s.role for s in result}
    names = [s.clothing_item.name for s in result]
    assert "tops" in roles
    assert "bottoms" in roles
    assert "onepiece" not in roles
    assert "plain onepiece" not in names


def test_onepiece_selected_when_no_tops_or_bottoms() -> None:
    """tops/bottoms 候補がない場合は onepiece が選ばれる"""
    onepiece = _make_clothing_item(
        "00000000-0000-0000-0000-000000000040",
        "ivory onepiece",
        "onepiece",
        ["date"],
    )

    result = OutfitService._select_clothes(tpo="date", clothes=[onepiece])

    assert len(result) == 1
    assert result[0].role == "onepiece"
    assert result[0].clothing_item.name == "ivory onepiece"


def test_regression_no_onepiece_selects_tops_and_bottoms() -> None:
    """onepiece 候補がない場合は従来どおり tops+bottoms が選ばれる"""
    tops = _make_clothing_item(
        "00000000-0000-0000-0000-000000000050",
        "plain tops",
        "tops",
        ["casual"],
    )
    bottoms = _make_clothing_item(
        "00000000-0000-0000-0000-000000000051",
        "plain bottoms",
        "bottoms",
        ["casual"],
    )

    result = OutfitService._select_clothes(tpo="casual", clothes=[tops, bottoms])

    roles = {s.role for s in result}
    assert "tops" in roles
    assert "bottoms" in roles
    assert "onepiece" not in roles


def test_suggest_outfit_rejects_tpo_exceeding_max_length(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "a" * 101},
    )

    assert response.status_code == 422


def test_suggest_outfit_rejects_too_many_clothing_ids(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    too_many_ids = [str(uuid.uuid4()) for _ in range(51)]
    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual", "clothing_ids": too_many_ids},
    )

    assert response.status_code == 422


def test_list_outfits_returns_items_and_total(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_list_outfits(db, user_id, **kwargs):
        assert user_id == uuid.UUID("00000000-0000-0000-0000-000000000001")
        assert kwargs == {"is_favorite": True, "limit": 1, "offset": 0}
        return type(
            "OutfitsListResponse",
            (),
            {
                "items": [
                    {
                        "id": uuid.UUID("00000000-0000-0000-0000-000000000777"),
                        "user_id": user_id,
                        "tpo": "casual",
                        "region_code": "13_01",
                        "weather_summary": "晴れ",
                        "weather_temp_max": 27.1,
                        "weather_temp_min": 19.8,
                        "comment": "generated-coordinate",
                        "coordinate_image_url": None,
                        "is_favorite": True,
                        "source": "llm",
                        "items": [],
                        "created_at": datetime(2026, 6, 4, tzinfo=UTC),
                    }
                ],
                "total": 3,
            },
        )()

    monkeypatch.setattr(outfits_router.outfits_crud, "list_outfits", fake_list_outfits)

    response = client.get("/api/v1/outfits", params={"limit": 1, "is_favorite": True})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "00000000-0000-0000-0000-000000000777",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "tpo": "casual",
                "region_code": "13_01",
                "weather_summary": "晴れ",
                "weather_temp_max": 27.1,
                "weather_temp_min": 19.8,
                "comment": "generated-coordinate",
                "coordinate_image_url": None,
                "is_favorite": True,
                "source": "llm",
                "items": [],
                "created_at": "2026-06-04T00:00:00Z",
            }
        ],
        "total": 3,
    }
