import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.outfit import Outfit, OutfitItem
from app.domain.outfits.service import SuggestedClothingSelection


async def create_suggested_outfit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tpo: str,
    region_code: str,
    weather_summary: str,
    weather_temp_max: float | None,
    weather_temp_min: float | None,
    comment: str | None,
    items: list[SuggestedClothingSelection],
) -> Outfit:
    outfit = Outfit(
        user_id=user_id,
        tpo=tpo,
        region_code=region_code,
        weather_summary=weather_summary,
        weather_temp_max=weather_temp_max,
        weather_temp_min=weather_temp_min,
        comment=comment,
        source="llm",
    )
    db.add(outfit)
    await db.flush()

    for item in items:
        db.add(
            OutfitItem(
                outfit_id=outfit.id,
                clothes_id=item.clothing_item.id,
                role=item.role,
                display_order=item.display_order,
            )
        )

    await db.commit()
    await db.refresh(outfit)
    return outfit
