import uuid
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

    assert result == "generated-coordinate"
    assert "casual" in captured["prompt"]
    assert "tops - white shirt - color=white" in captured["prompt"]
    assert "current: temp=25.0C" in captured["prompt"]


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
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        headers={"Authorization": "Bearer supabase-test-token"},
        json={
            "tpo": "casual",
            "date": "2026-06-04",
            "clothing_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            "exclude_clothing_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"coordinate": "generated-coordinate"}


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
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    response = client.post(
        "/api/v1/outfits/suggest",
        headers={"Authorization": "Bearer supabase-test-token"},
        json={"tpo": "casual"},
    )

    assert response.status_code == 200
    assert response.json() == {"coordinate": "generated-coordinate"}


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
        async def suggest(self, *, tpo: str, clothes: list[ClothingItem], weather: dict) -> str:
            del tpo, clothes, weather
            raise OutfitSuggestionError("failed to generate outfit suggestion")

    async def fake_fetch_weather_forecast(*, latitude: float, longitude: float, days: int):
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
