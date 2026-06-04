from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.outfits import (
    OutfitSuggestRequest,
    OutfitSuggestResponse,
)
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.outfits.service import OutfitService, OutfitSuggestionError

router = APIRouter(prefix="/outfits", tags=["Outfits"])


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.post(
    "/suggest",
    response_model=OutfitSuggestResponse,
)
async def suggest_outfit(
    request: OutfitSuggestRequest,
    current_user: AuthenticatedUser,
):
    del current_user

    service = OutfitService()

    try:
        result = await service.suggest(
            clothes=request.clothes,
            weather=request.weather,
        )
    except OutfitSuggestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to generate outfit suggestion",
        ) from exc

    return OutfitSuggestResponse(coordinate=result)
