from fastapi import APIRouter

from app.api.v1.schemas.outfits import (
    OutfitSuggestRequest,
    OutfitSuggestResponse,
)
from app.domain.outfits.service import OutfitService

router = APIRouter(prefix="/outfits", tags=["Outfits"])


@router.post(
    "/suggest",
    response_model=OutfitSuggestResponse,
)
async def suggest_outfit(
    request: OutfitSuggestRequest,
):
    service = OutfitService()

    result = await service.suggest(
        clothes=request.clothes,
        weather=request.weather,
    )

    return OutfitSuggestResponse(coordinate=result)
