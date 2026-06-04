from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.schemas.outfits import (
    OutfitSuggestRequest,
    OutfitSuggestResponse,
)
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.outfits.service import OutfitService

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

    result = await service.suggest(
        clothes=request.clothes,
        weather=request.weather,
    )

    return OutfitSuggestResponse(coordinate=result)
