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
from app.domain.outfits.service import OutfitService, OutfitSuggestionError
from app.services.weather_client import WeatherForecastResponseError


@pytest.mark.asyncio
async def test_outfit_service_uses_prompt_template_independent_of_cwd(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return "generated-coordinate"

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
                created_at="2026-06-04T00:00:00Z",
                updated_at="2026-06-04T00:00:00Z",
            )
        ],
        weather={
            "current": {
                "temperature_2m": 25.0,
                "weather_code": 1,
                "precipitation_probability": 10,
            },
            "daily": [
                {
                    "date": "2026-06-04",
                    "temperature_max": 27.0,
                    "temperature_min": 19.0,
                    "weather_code": 1,
                    "precipitation_probability_max": 10,
                }
            ],
        },
    )

    assert result.comment == "generated-coordinate"
    assert "casual" in captured["prompt"]
    assert "tops - white shirt - color=white" in captured["prompt"]
    assert "current: temp=25.0C" in captured["prompt"]
    assert result.weather_summary.startswith("current: temp=25.0C")
    assert [item.role for item in result.items] == ["tops"]


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
        *, latitude: float, longitude: float, days: int
    ):
        assert latitude == 35.6895
        assert longitude == 139.6917
        assert days == 3
        return {
            "current": {
                "temperature_2m": 25.4,
                "weather_code": 1,
                "precipitation_probability": 10,
            },
            "daily": [
                {
                    "date": "2026-06-04",
                    "temperature_max": 27.1,
                    "temperature_min": 19.8,
                    "weather_code": 1,
                    "precipitation_probability_max": 10,
                }
            ],
            "cached": False,
        }

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
                        created_at="2026-06-04T00:00:00Z",
                        updated_at="2026-06-04T00:00:00Z",
                    )
                ]
            },
        )()

    async def fake_create_suggested_outfit(
        db,
        *,
        user_id,
        tpo,
        region_code,
        weather_summary,
        weather_temp_max,
        weather_temp_min,
        comment,
        items,
    ):
        assert user_id == resolved_user_id
        assert tpo == "casual"
        assert region_code == "13_01"
        assert weather_temp_max == 27.1
        assert weather_temp_min == 19.8
        assert comment == "generated-coordinate"
        assert [item.role for item in items] == ["tops"]
        return type(
            "Outfit",
            (),
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000777"),
                "is_favorite": False,
                "source": "llm",
                "created_at": datetime(2026, 6, 4, tzinfo=UTC),
            },
        )()

    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            assert "casual" in prompt
            assert "current: temp=25.4C" in prompt
            assert "tops - white shirt - color=white" in prompt
            assert "2026-06-04" in prompt
            return "generated-coordinate"

    monkeypatch.setattr(
        "app.dependencies.auth.verify_supabase_jwt", fake_verify_supabase_jwt
    )
    monkeypatch.setattr(
        "app.dependencies.auth.user_crud.get_or_create_user", fake_get_or_create_user
    )
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)
    monkeypatch.setattr(
        outfits_router.outfits_crud,
        "create_suggested_outfit",
        fake_create_suggested_outfit,
    )
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
    assert response.json() == {
        "outfits": [
            {
                "id": "00000000-0000-0000-0000-000000000777",
                "user_id": str(resolved_user_id),
                "tpo": "casual",
                "region_code": "13_01",
                "weather_summary": (
                    "current: temp=25.4C, weather_code=1, "
                    "precipitation_probability=10%\n"
                    "2026-06-04: max=27.1C, min=19.8C, weather_code=1, "
                    "precipitation_probability_max=10%"
                ),
                "weather_temp_max": 27.1,
                "weather_temp_min": 19.8,
                "comment": "generated-coordinate",
                "is_favorite": False,
                "source": "llm",
                "items": [
                    {
                        "clothes_id": "00000000-0000-0000-0000-000000000010",
                        "role": "tops",
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
                ],
                "created_at": "2026-06-04T00:00:00Z",
            }
        ],
        "weather_summary": (
            "current: temp=25.4C, weather_code=1, precipitation_probability=10%\n"
            "2026-06-04: max=27.1C, min=19.8C, weather_code=1, "
            "precipitation_probability_max=10%"
        ),
        "region_used": {
            "code": "13_01",
            "prefecture_code": "13",
            "prefecture_name": "東京都",
            "name": "23区",
            "city": "新宿区",
            "latitude": 35.6895,
            "longitude": 139.6917,
        },
        "cached": False,
    }


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
        *, latitude: float, longitude: float, days: int
    ):
        expected_coordinates = get_region_coordinates("13_01")
        assert expected_coordinates is not None
        assert (latitude, longitude) == expected_coordinates
        return {
            "current": {
                "temperature_2m": 20.0,
                "weather_code": 2,
                "precipitation_probability": 20,
            },
            "daily": [],
            "cached": False,
        }

    async def fake_list_clothes(db, user_id, **kwargs):
        return type("ClothesListResponse", (), {"items": []})()

    async def fake_create_suggested_outfit(
        db,
        *,
        user_id,
        tpo,
        region_code,
        weather_summary,
        weather_temp_max,
        weather_temp_min,
        comment,
        items,
    ):
        assert region_code == "13_01"
        assert items == []
        return type(
            "Outfit",
            (),
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000888"),
                "is_favorite": False,
                "source": "llm",
                "created_at": datetime(2026, 6, 4, tzinfo=UTC),
            },
        )()

    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            assert "服の登録はありません。" in prompt
            return "generated-coordinate"

    monkeypatch.setattr(
        "app.dependencies.auth.verify_supabase_jwt", fake_verify_supabase_jwt
    )
    monkeypatch.setattr(
        "app.dependencies.auth.user_crud.get_or_create_user", fake_get_or_create_user
    )
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(outfits_router.clothes_crud, "list_clothes", fake_list_clothes)
    monkeypatch.setattr(
        outfits_router.outfits_crud,
        "create_suggested_outfit",
        fake_create_suggested_outfit,
    )
    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        headers={"Authorization": "Bearer supabase-test-token"},
        json={"tpo": "casual"},
    )

    assert response.status_code == 200
    assert response.json()["region_used"]["code"] == "13_01"
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
def test_suggest_outfit_rejects_unsupported_clothing_filters(
    client: TestClient,
    monkeypatch,
    payload: dict[str, object],
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    response = client.post("/api/v1/outfits/suggest", json=payload)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "clothing_ids and exclude_clothing_ids are not supported"
    )


@pytest.mark.asyncio
async def test_outfit_service_wraps_llm_api_errors(monkeypatch) -> None:
    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            del prompt
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
            weather={
                "current": {
                    "temperature_2m": 25.0,
                    "weather_code": 1,
                    "precipitation_probability": 10,
                },
                "daily": [],
            },
        )

    assert str(exc_info.value) == "failed to generate outfit suggestion"
    assert isinstance(exc_info.value.__cause__, APIError)


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
            self, *, tpo: str, clothes: list[ClothingItem], weather: dict
        ) -> str:
            del tpo, clothes, weather
            raise OutfitSuggestionError("failed to generate outfit suggestion")

    async def fake_fetch_weather_forecast(
        *, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        return {
            "current": {
                "temperature_2m": 25.0,
                "weather_code": 1,
                "precipitation_probability": 10,
            },
            "daily": [],
        }

    async def fake_list_clothes(db, user_id, **kwargs):
        del db, user_id, kwargs
        return type("ClothesListResponse", (), {"items": []})()

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr("app.api.v1.routers.outfits.OutfitService", FakeOutfitService)
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast", fake_fetch_weather_forecast
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
        *, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        return {
            "current": {
                "temperature_2m": 25.0,
                "weather_code": 1,
                "precipitation_probability": 10,
            },
            "daily": [],
        }

    async def fake_list_clothes(db, user_id, **kwargs):
        del db, user_id, kwargs
        return type("ClothesListResponse", (), {"items": []})()

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr("app.api.v1.routers.outfits.OutfitService", FakeOutfitService)
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast", fake_fetch_weather_forecast
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
        *, latitude: float, longitude: float, days: int
    ):
        del latitude, longitude, days
        raise WeatherForecastResponseError("invalid weather forecast response")

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(
        outfits_router, "fetch_weather_forecast", fake_fetch_weather_forecast
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"tpo": "casual"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to fetch weather forecast"


@pytest.mark.asyncio
async def test_onepiece_selected_over_tops_on_equal_score(
    monkeypatch,
) -> None:
    """同スコアのとき onepiece が tops より優先される (Issue #60)"""
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return "generated-coordinate"

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    service = OutfitService()

    tops_item = ClothingItem(
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
        created_at="2026-06-04T00:00:00Z",
        updated_at="2026-06-04T00:00:00Z",
    )
    onepiece_item = ClothingItem(
        id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="floral onepiece",
        category="onepiece",
        color="pink",
        pattern=None,
        size="M",
        season=["spring", "summer"],
        tpo_tags=["casual"],
        image_url="https://example.com/onepiece.jpg",
        thumbnail_url=None,
        memo=None,
        is_favorite=False,
        wear_count=0,
        last_worn_at=None,
        created_at="2026-06-04T00:00:00Z",
        updated_at="2026-06-04T00:00:00Z",
    )

    result = await service.suggest(
        tpo="casual",
        clothes=[tops_item, onepiece_item],
        weather={
            "current": {
                "temperature_2m": 25.0,
                "weather_code": 1,
                "precipitation_probability": 10,
            },
            "daily": [],
        },
    )

    assert "floral onepiece" in captured["prompt"]
    assert "white shirt" not in captured["prompt"]
    item_names = [s.clothing_item.name for s in result.items]
    assert "floral onepiece" in item_names
    assert "white shirt" not in item_names


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
        created_at="2026-06-04T00:00:00Z",
        updated_at="2026-06-04T00:00:00Z",
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
                "is_favorite": True,
                "source": "llm",
                "items": [],
                "created_at": "2026-06-04T00:00:00Z",
            }
        ],
        "total": 3,
    }
