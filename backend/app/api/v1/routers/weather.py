from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.regions import to_region_schema
from app.api.v1.schemas.weather import WeatherForecast
from app.constants.regions import get_region_coordinates
from app.core.logging import logger
from app.dependencies.auth import CurrentUser, get_current_user
from app.services.weather_client import (
    WeatherForecastResponseError,
    fetch_weather_forecast_cached,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/forecast", response_model=WeatherForecast)
async def get_weather_forecast(
    region_code: str,
    current_user: AuthenticatedUser,
    days: int = Query(default=3, ge=1, le=7),
) -> WeatherForecast:
    del current_user

    coordinates = get_region_coordinates(region_code)
    if coordinates is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )

    latitude, longitude = coordinates

    try:
        forecast = await fetch_weather_forecast_cached(
            region_code=region_code,
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
    except httpx.HTTPError as exc:
        logger.error(
            "weather fetch failed (region=%s, days=%s): %s", region_code, days, exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to fetch weather forecast",
        ) from exc
    except WeatherForecastResponseError as exc:
        logger.error(
            "weather forecast invalid (region=%s, days=%s): %s", region_code, days, exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to fetch weather forecast",
        ) from exc

    return WeatherForecast(
        region_code=region_code,
        region=to_region_schema(region_code),
        **forecast,
    )
