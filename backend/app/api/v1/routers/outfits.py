from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.outfits import (
    OutfitSuggestRequest,
    OutfitSuggestResponse,
)
from app.constants.regions import get_region_coordinates
from app.core.deps import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.clothes import crud as clothes_crud
from app.domain.outfits.service import OutfitService, OutfitSuggestionError
from app.services.weather_client import fetch_weather_forecast

router = APIRouter(prefix="/outfits", tags=["Outfits"])


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
DEFAULT_REGION_CODE = "13_01"
CLOTHES_FETCH_LIMIT = 1000


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

    coordinates = get_region_coordinates(region_code)
    if coordinates is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )

    latitude, longitude = coordinates

    try:
        weather = await fetch_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            days=3,
        )
    except httpx.HTTPError as exc:
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

    service = OutfitService()

    try:
        result = await service.suggest(
            tpo=request.tpo,
            clothes=clothes,
            weather=weather,
        )
    except OutfitSuggestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to generate outfit suggestion",
        ) from exc

    return OutfitSuggestResponse(coordinate=result)
