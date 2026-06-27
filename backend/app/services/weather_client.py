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
HOURLY_FIELDS = "precipitation_probability"

# 当日の降水確率を「朝/昼/夜」に分けて評価するためのローカル時刻の窓（時）。
# 「忙しい朝」に傘要否を判断できるよう、各窓は最大値（安全側）で代表させる。
# 当日コーデ提案が目的のため 22-23 時・深夜帯は意図的に対象外（どの窓にも入れない）。
_PART_WINDOWS: dict[str, range] = {
    "morning": range(6, 12),
    "afternoon": range(12, 18),
    "evening": range(18, 22),
}


class WeatherForecastResponseError(Exception):
    """Open-Meteo のレスポンス形式が想定外の場合のエラー。"""


class OutfitPromptWeather(TypedDict):
    current_temperature: float
    current_weather: str
    today_weather: str
    today_temperature_max: float
    today_temperature_min: float
    today_precipitation_probability: int
    # 当日の時間帯別降水確率（各窓の最大値）。時間別データが無い場合は日最大で代替。
    today_precipitation_morning: int
    today_precipitation_afternoon: int
    today_precipitation_evening: int


def _precipitation_by_part(hourly: dict[str, Any], today: str) -> dict[str, int]:
    """時間別降水確率から、当日の朝/昼/夜それぞれの最大降水確率を求める。

    Open-Meteo の hourly.time は timezone=auto によりローカル時刻の ISO 文字列
    （例: "2026-06-26T06:00"）。当日分のみを対象に窓ごとの最大値を返す。
    データが無い窓は結果に含めない（呼び出し側で日最大に代替）。
    """
    times = hourly.get("time") or []
    probs = hourly.get("precipitation_probability") or []
    buckets: dict[str, list[int]] = {part: [] for part in _PART_WINDOWS}
    for time_str, prob in zip(times, probs, strict=False):
        if not isinstance(time_str, str) or not time_str.startswith(today):
            continue
        if prob is None:
            continue
        try:
            hour = int(time_str[11:13])
        except (ValueError, IndexError):
            continue
        for part, window in _PART_WINDOWS.items():
            if hour in window:
                buckets[part].append(prob)
                break
    return {part: max(values) for part, values in buckets.items() if values}


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
        daily_max = today["precipitation_probability_max"]
        # 時間別が無い窓は日最大で代替（旧キャッシュ・hourly 欠落時も安全）。
        by_part = forecast.get("today_precipitation_by_part") or {}
        return {
            "current_temperature": current["temperature_2m"],
            "current_weather": get_weather_label(current["weather_code"]),
            "today_weather": get_weather_label(today["weather_code"]),
            "today_temperature_max": today["temperature_max"],
            "today_temperature_min": today["temperature_min"],
            "today_precipitation_probability": daily_max,
            "today_precipitation_morning": by_part.get("morning", daily_max),
            "today_precipitation_afternoon": by_part.get("afternoon", daily_max),
            "today_precipitation_evening": by_part.get("evening", daily_max),
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
        "hourly": HOURLY_FIELDS,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_FORECAST_URL, params=params)
        response.raise_for_status()

    try:
        payload = response.json()
        current = payload["current"]
        daily = payload["daily"]
        # 当日の朝/昼/夜の降水確率（hourly は任意。欠落しても提案は継続できる）。
        today_date = daily["time"][0]
        by_part = _precipitation_by_part(payload.get("hourly") or {}, today_date)

        return {
            "current": {
                "temperature_2m": current["temperature_2m"],
                "weather_code": current["weather_code"],
                "precipitation_probability": current["precipitation_probability"],
            },
            "today_precipitation_by_part": by_part,
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
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        # daily["time"] が空（IndexError）/想定外型（TypeError）でも欠損レスポンス扱いで
        # 正規化する（上の解析関数と捕捉範囲を揃える）。
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
