from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import httpx

from app.core.config import settings
from app.core.redis import cache_get_json, cache_set_json

# 天気キャッシュキーの日付は JST 基準（日付境界をアプリのタイムゾーンに合わせる）。
_JST = timezone(timedelta(hours=9))

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max"
)


class WeatherForecastResponseError(Exception):
    """Open-Meteo のレスポンス形式が想定外の場合のエラー。"""


class OutfitPromptWeather(TypedDict):
    current_temperature: float
    current_weather: str
    today_weather: str
    today_temperature_max: float
    today_temperature_min: float
    today_precipitation_probability: int


def get_weather_label(weather_code: int) -> str:
    if weather_code == 0:
        return "快晴"

    if weather_code == 1:
        return "晴れ"

    if weather_code == 2:
        return "くもり時々晴れ"

    if weather_code == 3:
        return "くもり"

    if weather_code in {45, 48}:
        return "霧"

    if weather_code in {51, 53, 55, 56, 57}:
        return "霧雨"

    if weather_code in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "雨"

    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "雪"

    if weather_code in {95, 96, 99}:
        return "雷雨"

    return "不明"


def extract_outfit_prompt_weather(forecast: dict[str, Any]) -> OutfitPromptWeather:
    try:
        current = forecast["current"]
        today = forecast["daily"][0]
        return {
            "current_temperature": current["temperature_2m"],
            "current_weather": get_weather_label(current["weather_code"]),
            "today_weather": get_weather_label(today["weather_code"]),
            "today_temperature_max": today["temperature_max"],
            "today_temperature_min": today["temperature_min"],
            "today_precipitation_probability": today["precipitation_probability_max"],
        }
    except (IndexError, KeyError, TypeError) as exc:
        raise WeatherForecastResponseError("invalid weather forecast response") from exc


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


async def fetch_weather_forecast_cached(
    *, region_code: str, latitude: float, longitude: float, days: int
) -> dict[str, Any]:
    """Redis キャッシュ対応の天気取得。

    ヒット時は Open-Meteo を呼ばず保存値を返す（`cached=True`）。ミス時は
    `fetch_weather_forecast` で取得し、結果を TTL 付きで保存する（`cached=False`）。
    Redis 障害時はキャッシュミス扱いで処理を継続する（cache_get/set 側で握りつぶし）。

    キー: `weather:{region_code}:{yyyymmdd}:{days}`（仕様 docs/openapi.yaml 準拠。
    days は予報日数で結果が変わるため衝突回避に含める）。
    """
    yyyymmdd = datetime.now(_JST).strftime("%Y%m%d")
    key = f"weather:{region_code}:{yyyymmdd}:{days}"

    cached = await cache_get_json(key)
    if cached is not None:
        cached["cached"] = True
        return cached

    payload = await fetch_weather_forecast(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )
    await cache_set_json(key, payload, settings.REDIS_WEATHER_TTL_SECONDS)
    return payload
