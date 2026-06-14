from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.outfits import (
    OutfitsListResponse,
    OutfitSuggestRequest,
    OutfitSuggestResponse,
    SuggestedOutfit,
    SuggestedOutfitItem,
)
from app.api.v1.schemas.regions import Region
from app.constants.regions import get_region
from app.core.deps import get_db
from app.core.logging import logger
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.clothes import crud as clothes_crud
from app.domain.outfits import crud as outfits_crud
from app.domain.outfits.service import OutfitService, OutfitSuggestionError
from app.services.weather_client import (
    WeatherForecastResponseError,
    fetch_weather_forecast_cached,
)

router = APIRouter(prefix="/outfits", tags=["Outfits"])


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
DEFAULT_REGION_CODE = "13_01"
CLOTHES_FETCH_LIMIT = 1000


@router.get("", response_model=OutfitsListResponse)
async def list_outfits(
    current_user: AuthenticatedUser,
    db: DbSession,
    is_favorite: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OutfitsListResponse:
    return await outfits_crud.list_outfits(
        db,
        current_user.id,
        is_favorite=is_favorite,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/suggest",
    response_model=OutfitSuggestResponse,
)
async def suggest_outfit(
    request: OutfitSuggestRequest,
    current_user: AuthenticatedUser,
    db: DbSession,
):
    region_code = (
        request.region_code or current_user.default_region_code or DEFAULT_REGION_CODE
    )

    region = get_region(region_code)
    if region is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )

    latitude, longitude = region["lat"], region["lng"]

    try:
        weather = await fetch_weather_forecast_cached(
            region_code=region_code,
            latitude=latitude,
            longitude=longitude,
            days=3,
        )
    except httpx.HTTPError as exc:
        logger.error("weather fetch failed (region=%s): %s", region_code, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to fetch weather forecast",
        ) from exc
    except WeatherForecastResponseError as exc:
        logger.error("weather forecast invalid (region=%s): %s", region_code, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to fetch weather forecast",
        ) from exc

    clothes = (
        await clothes_crud.list_clothes(
            db,
            current_user.id,
            limit=CLOTHES_FETCH_LIMIT,
            offset=0,
        )
    ).items

    try:
        service = OutfitService()
        result = await service.suggest(
            tpo=request.tpo,
            clothes=clothes,
            weather=weather,
            clothing_ids=request.clothing_ids,
            exclude_clothing_ids=request.exclude_clothing_ids,
        )
    except OutfitSuggestionError as exc:
        logger.error(
            "outfit suggestion failed (user=%s, tpo=%s): %s",
            current_user.id,
            request.tpo,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to generate outfit suggestion",
        ) from exc

    today_forecast = weather.get("daily", [{}])[0] if weather.get("daily") else {}
    saved_outfit = await outfits_crud.create_suggested_outfit(
        db,
        user_id=current_user.id,
        tpo=request.tpo,
        region_code=region_code,
        weather_summary=result.weather_summary,
        weather_temp_max=today_forecast.get("temperature_max"),
        weather_temp_min=today_forecast.get("temperature_min"),
        comment=result.comment,
        courage_image_url="",  # TODO: 生成されたコーデ画像のURLを保存する
        items=result.items,
    )

    logger.info(
        "outfit suggested (user=%s, outfit=%s, region=%s, items=%d)",
        current_user.id,
        saved_outfit.id,
        region_code,
        len(result.items),
    )

    return OutfitSuggestResponse(
        outfits=[
            SuggestedOutfit(
                id=saved_outfit.id,
                user_id=current_user.id,
                tpo=request.tpo,
                region_code=region_code,
                weather_summary=result.weather_summary,
                weather_temp_max=today_forecast.get("temperature_max"),
                weather_temp_min=today_forecast.get("temperature_min"),
                comment=result.comment,
                courage_image_url=saved_outfit.courage_image_url,
                is_favorite=saved_outfit.is_favorite,
                source=saved_outfit.source,
                items=[
                    SuggestedOutfitItem(
                        clothes_id=item.clothing_item.id,
                        role=item.role,
                        display_order=item.display_order,
                        clothing_item=item.clothing_item,
                    )
                    for item in result.items
                ],
                created_at=saved_outfit.created_at,
            )
        ],
        weather_summary=result.weather_summary,
        region_used=Region(
            code=region_code,
            prefecture_code=region_code.split("_")[0],
            prefecture_name=region["prefecture"],
            name=region["name"],
            city=region["city"],
            latitude=region["lat"],
            longitude=region["lng"],
        ),
        # cached は「提案結果キャッシュ」（suggest:... TTL24h）由来を示す仕様。
        # 天気キャッシュがヒットしても LLM 提案と DB 保存は毎回走るため、
        # 提案結果キャッシュ未実装の現状は常に False（天気キャッシュとは別概念）。
        cached=False,
    )
