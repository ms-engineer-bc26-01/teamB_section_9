import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas.clothes import (
    ClothingCreateRequest,
    ClothingItem,
    ClothingUpdateRequest,
    ClothesListResponse,
)
from app.db.models.clothes import Clothes, ClothesTpo


def _base_query(user_id: uuid.UUID):
    return (
        select(Clothes)
        .where(Clothes.user_id == user_id)
        .options(selectinload(Clothes.tpo_tags))
    )


def _to_schema(item: Clothes) -> ClothingItem:
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


async def list_clothes(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    category: str | None = None,
    season: str | None = None,
    tpo: str | None = None,
    is_favorite: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ClothesListResponse:
    filters = [Clothes.user_id == user_id]
    if category is not None:
        filters.append(Clothes.category == category)
    if season is not None:
        filters.append(Clothes.season.any(season))
    if tpo is not None:
        filters.append(Clothes.tpo_tags.any(ClothesTpo.tpo_tag == tpo))
    if is_favorite is not None:
        filters.append(Clothes.is_favorite == is_favorite)

    total = await db.scalar(select(func.count()).select_from(Clothes).where(*filters)) or 0
    items = (
        await db.scalars(
        select(Clothes)
        .where(*filters)
        .options(selectinload(Clothes.tpo_tags))
        .order_by(Clothes.created_at.desc())
        .limit(limit)
        .offset(offset)
        )
    ).all()

    return ClothesListResponse(items=[_to_schema(item) for item in items], total=total)


async def get_clothing_or_404(
    db: AsyncSession,
    user_id: uuid.UUID,
    clothing_id: uuid.UUID,
) -> Clothes:
    item = await db.scalar(
        _base_query(user_id).where(Clothes.id == clothing_id)
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="clothing not found",
        )
    return item


async def get_clothing(
    db: AsyncSession,
    user_id: uuid.UUID,
    clothing_id: uuid.UUID,
) -> ClothingItem:
    return _to_schema(await get_clothing_or_404(db, user_id, clothing_id))


async def create_clothing(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: ClothingCreateRequest,
) -> ClothingItem:
    item = Clothes(
        user_id=user_id,
        name=payload.name,
        category=payload.category,
        color=payload.color,
        pattern=payload.pattern,
        size=payload.size,
        season=payload.season,
        image_url=payload.image_url,
        thumbnail_url=payload.thumbnail_url,
        memo=payload.memo,
        is_favorite=payload.is_favorite,
    )
    item.tpo_tags = [ClothesTpo(tpo_tag=tag) for tag in payload.tpo_tags]

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return _to_schema(await get_clothing_or_404(db, user_id, item.id))


async def update_clothing(
    db: AsyncSession,
    user_id: uuid.UUID,
    clothing_id: uuid.UUID,
    payload: ClothingUpdateRequest,
) -> ClothingItem:
    item = await get_clothing_or_404(db, user_id, clothing_id)
    updates = payload.model_dump(exclude_unset=True)

    tpo_tags = updates.pop("tpo_tags", None)
    for field, value in updates.items():
        setattr(item, field, value)

    if tpo_tags is not None:
        item.tpo_tags = [ClothesTpo(tpo_tag=tag) for tag in tpo_tags]

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return _to_schema(await get_clothing_or_404(db, user_id, clothing_id))


async def delete_clothing(
    db: AsyncSession,
    user_id: uuid.UUID,
    clothing_id: uuid.UUID,
) -> None:
    item = await get_clothing_or_404(db, user_id, clothing_id)
    await db.delete(item)
    await db.commit()