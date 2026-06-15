import uuid
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.outfits import (
    OutfitsListResponse,
    OutfitSuggestRequest,
    OutfitSuggestResponse,
    SuggestedGeneratedOutfit,
    SuggestedGeneratedOutfitItem,
)
from app.constants.regions import get_region
from app.core.deps import get_db
from app.core.logging import logger
from app.dependencies.auth import CurrentUser, get_current_user
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

    try:
        service = OutfitService()
        result = await service.suggest(
            tpo=request.tpo,
            clothes=[],
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

    logger.info(
        "outfit suggested (user=%s, region=%s, items=%d)",
        current_user.id,
        region_code,
        len(result.items),
    )

    return OutfitSuggestResponse(
        outfits=[
            SuggestedGeneratedOutfit(
                id=uuid.uuid4(),
                user_id=current_user.id,
                tpo=request.tpo,
                comment=result.comment,
                is_favorite=False,
                items=[
                    SuggestedGeneratedOutfitItem(
                        name=item.name,
                        role=item.role,
                        color=item.color,
                        pattern=item.pattern,
                        display_order=item.display_order,
                        clothing_item=item.clothing_item,
                    )
                    for item in result.items
                ],
                created_at=datetime.now(UTC),
            )
        ]
    )
