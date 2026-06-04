from typing import Any

import httpx

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max"
)


class WeatherForecastResponseError(Exception):
    """Open-Meteo のレスポンス形式が想定外の場合のエラー。"""


async def fetch_weather_forecast(
    *, latitude: float, longitude: float, days: int
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": days,
        "current": "temperature_2m,weather_code,precipitation_probability",
        "daily": DAILY_FIELDS,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_FORECAST_URL, params=params)
        response.raise_for_status()

    try:
        payload = response.json()
        current = payload["current"]
        daily = payload["daily"]

        return {
            "current": {
                "temperature_2m": current["temperature_2m"],
                "weather_code": current["weather_code"],
                "precipitation_probability": current["precipitation_probability"],
            },
            "daily": [
                {
                    "date": date,
                    "temperature_max": temperature_max,
                    "temperature_min": temperature_min,
                    "weather_code": weather_code,
                    "precipitation_probability_max": precipitation_probability_max,
                }
                for (
                    date,
                    temperature_max,
                    temperature_min,
                    weather_code,
                    precipitation_probability_max,
                ) in zip(
                    daily["time"],
                    daily["temperature_2m_max"],
                    daily["temperature_2m_min"],
                    daily["weather_code"],
                    daily["precipitation_probability_max"],
                    strict=True,
                )
            ],
            "cached": False,
        }
    except (KeyError, ValueError) as exc:
        raise WeatherForecastResponseError("invalid weather forecast response") from exc
