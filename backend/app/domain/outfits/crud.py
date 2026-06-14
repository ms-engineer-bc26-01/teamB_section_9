import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas.clothes import ClothingItem
from app.api.v1.schemas.outfits import (
    OutfitsListResponse,
    SuggestedOutfit,
    SuggestedOutfitItem,
)
from app.db.models.clothes import Clothes
from app.db.models.outfit import Outfit, OutfitItem
from app.domain.outfits.service import SuggestedClothingSelection


def _to_clothing_schema(item: Clothes) -> ClothingItem:
    return ClothingItem(
        id=item.id,
        user_id=item.user_id,
        name=item.name,
        category=item.category,
        color=item.color,
        pattern=item.pattern,
        size=item.size,
        season=item.season,
        tpo_tags=[tag.tpo_tag for tag in item.tpo_tags],
        image_url=item.image_url,
        thumbnail_url=item.thumbnail_url,
        memo=item.memo,
        is_favorite=item.is_favorite,
        wear_count=item.wear_count,
        last_worn_at=item.last_worn_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_outfit_schema(outfit: Outfit) -> SuggestedOutfit:
    return SuggestedOutfit(
        id=outfit.id,
        user_id=outfit.user_id,
        tpo=outfit.tpo,
        region_code=outfit.region_code,
        weather_summary=outfit.weather_summary,
        weather_temp_max=outfit.weather_temp_max,
        weather_temp_min=outfit.weather_temp_min,
        comment=outfit.comment,
        courage_image_url=outfit.courage_image_url,
        is_favorite=outfit.is_favorite,
        source=outfit.source,
        items=[
            SuggestedOutfitItem(
                clothes_id=item.clothes_id,
                role=item.role,
                display_order=item.display_order,
                clothing_item=_to_clothing_schema(item.clothes),
            )
            for item in sorted(outfit.items, key=lambda item: item.display_order)
        ],
        created_at=outfit.created_at,
    )


async def list_outfits(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    is_favorite: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> OutfitsListResponse:
    filters = [Outfit.user_id == user_id]

    if is_favorite is not None:
        filters.append(Outfit.is_favorite == is_favorite)

    total = (
        await db.scalar(select(func.count()).select_from(Outfit).where(*filters)) or 0
    )

    outfits = (
        await db.scalars(
            select(Outfit)
            .where(*filters)
            .options(
                selectinload(Outfit.items)
                .selectinload(OutfitItem.clothes)
                .selectinload(Clothes.tpo_tags)
            )
            .order_by(Outfit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    return OutfitsListResponse(
        items=[_to_outfit_schema(outfit) for outfit in outfits],
        total=total,
    )


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
    courage_image_url: str | None,
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
        courage_image_url=courage_image_url,
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
