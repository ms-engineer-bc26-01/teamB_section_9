import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routers import weather as weather_router
from app.dependencies import auth
from app.services import weather_client
from app.services.weather_client import (
    WeatherForecastResponseError,
    fetch_weather_forecast_cached,
)


def _auth_headers(token: str = "supabase-test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mock_supabase_user(monkeypatch) -> uuid.UUID:
    resolved_user_id = uuid.UUID("00000000-0000-0000-0000-000000000123")

    async def fake_verify_supabase_jwt(token: str) -> dict[str, object]:
        assert token == "supabase-test-token"
        return {
            "sub": str(resolved_user_id),
            "email": "jwt-user@example.com",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "exp": 9999999999,
        }

    async def fake_get_or_create_user(db, *, user_id, email):
        return type("User", (), {"id": user_id, "email": email})()

    monkeypatch.setattr(auth, "verify_supabase_jwt", fake_verify_supabase_jwt)
    monkeypatch.setattr(auth.user_crud, "get_or_create_user", fake_get_or_create_user)
    return resolved_user_id


def test_get_weather_forecast_returns_open_meteo_data(
    client: TestClient,
    monkeypatch,
) -> None:
    _mock_supabase_user(monkeypatch)

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
                    "date": "2026-06-01",
                    "temperature_max": 27.1,
                    "temperature_min": 19.8,
                    "weather_code": 1,
                    "precipitation_probability_max": 10,
                },
                {
                    "date": "2026-06-02",
                    "temperature_max": 28.0,
                    "temperature_min": 20.1,
                    "weather_code": 2,
                    "precipitation_probability_max": 20,
                },
                {
                    "date": "2026-06-03",
                    "temperature_max": 24.5,
                    "temperature_min": 18.7,
                    "weather_code": 61,
                    "precipitation_probability_max": 70,
                },
            ],
            "cached": False,
        }

    monkeypatch.setattr(
        weather_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )

    response = client.get(
        "/api/v1/weather/forecast",
        params={"region_code": "13_01"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "region_code": "13_01",
        "current": {
            "temperature_2m": 25.4,
            "weather_code": 1,
            "precipitation_probability": 10,
        },
        "daily": [
            {
                "date": "2026-06-01",
                "temperature_max": 27.1,
                "temperature_min": 19.8,
                "weather_code": 1,
                "precipitation_probability_max": 10,
            },
            {
                "date": "2026-06-02",
                "temperature_max": 28.0,
                "temperature_min": 20.1,
                "weather_code": 2,
                "precipitation_probability_max": 20,
            },
            {
                "date": "2026-06-03",
                "temperature_max": 24.5,
                "temperature_min": 18.7,
                "weather_code": 61,
                "precipitation_probability_max": 70,
            },
        ],
        "cached": False,
    }


def test_get_weather_forecast_returns_400_for_unknown_region(
    client: TestClient,
    monkeypatch,
) -> None:
    _mock_supabase_user(monkeypatch)

    async def fail_if_called(**kwargs):
        raise AssertionError("fetch_weather_forecast_cached should not be called")

    monkeypatch.setattr(
        weather_router, "fetch_weather_forecast_cached", fail_if_called
    )

    response = client.get(
        "/api/v1/weather/forecast",
        params={"region_code": "99_99"},
        headers=_auth_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid region_code"


def test_get_weather_forecast_returns_502_for_invalid_open_meteo_response(
    client: TestClient,
    monkeypatch,
) -> None:
    _mock_supabase_user(monkeypatch)

    async def fake_fetch_weather_forecast(**kwargs):
        raise WeatherForecastResponseError("invalid weather forecast response")

    monkeypatch.setattr(
        weather_router, "fetch_weather_forecast_cached", fake_fetch_weather_forecast
    )

    response = client.get(
        "/api/v1/weather/forecast",
        params={"region_code": "13_01"},
        headers=_auth_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to fetch weather forecast"


def test_get_weather_forecast_rejects_days_over_maximum(
    client: TestClient,
    monkeypatch,
) -> None:
    _mock_supabase_user(monkeypatch)

    response = client.get(
        "/api/v1/weather/forecast",
        params={"region_code": "13_01", "days": 8},
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_get_weather_forecast_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/weather/forecast",
        params={"region_code": "13_01"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_fetch_weather_forecast_cached_miss_fetches_and_stores(
    monkeypatch,
) -> None:
    """ミス時: Open-Meteo を呼んで保存し、cached=False を返す。"""
    fetched: list[bool] = []
    stored: list[tuple] = []

    async def fake_cache_get_json(key: str):
        return None

    async def fake_fetch_weather_forecast(*, latitude, longitude, days):
        fetched.append(True)
        return {"current": {}, "daily": [], "cached": False}

    async def fake_cache_set_json(key, value, ttl_seconds):
        stored.append((key, value, ttl_seconds))

    monkeypatch.setattr(weather_client, "cache_get_json", fake_cache_get_json)
    monkeypatch.setattr(
        weather_client, "fetch_weather_forecast", fake_fetch_weather_forecast
    )
    monkeypatch.setattr(weather_client, "cache_set_json", fake_cache_set_json)

    result = await fetch_weather_forecast_cached(
        latitude=1.0, longitude=2.0, days=3
    )

    assert result["cached"] is False
    assert fetched == [True]
    assert stored[0][0] == "weather:1.0:2.0:3"


@pytest.mark.asyncio
async def test_fetch_weather_forecast_cached_hit_skips_fetch(monkeypatch) -> None:
    """ヒット時: Open-Meteo を呼ばず、cached=True を返す。"""

    async def fake_cache_get_json(key: str):
        assert key == "weather:1.0:2.0:3"
        return {"current": {}, "daily": [], "cached": False}

    async def fail_if_called(**kwargs):
        raise AssertionError("fetch_weather_forecast should not be called on hit")

    monkeypatch.setattr(weather_client, "cache_get_json", fake_cache_get_json)
    monkeypatch.setattr(weather_client, "fetch_weather_forecast", fail_if_called)

    result = await fetch_weather_forecast_cached(
        latitude=1.0, longitude=2.0, days=3
    )

    assert result["cached"] is True
