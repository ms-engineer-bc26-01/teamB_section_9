import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas.clothes import ClothingItem
from app.api.v1.schemas.outfits import (
    OutfitCreateItem,
    OutfitsListResponse,
    SuggestedOutfit,
    SuggestedOutfitItem,
)
from app.db.models.clothes import Clothes
from app.db.models.outfit import Outfit, OutfitItem


class OutfitItemNotOwnedError(Exception):
    """保存リクエストの clothes_id にユーザー所有でない服が含まれる。"""

    def __init__(self, clothes_ids: set[uuid.UUID]) -> None:
        self.clothes_ids = clothes_ids
        super().__init__(f"clothes not owned: {sorted(str(c) for c in clothes_ids)}")


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


def _to_outfit_item_schema(item: OutfitItem) -> SuggestedOutfitItem:
    # owned: 手持ち服を join 解決し、表示フィールドは DB 値を正とする。
    if item.clothes is not None:
        clothing_item = _to_clothing_schema(item.clothes)
        return SuggestedOutfitItem(
            name=clothing_item.name,
            role=item.role,
            color=clothing_item.color,
            pattern=clothing_item.pattern,
            display_order=item.display_order,
            clothing_item=clothing_item,
        )
    # suggested（または手持ち服が削除済み）: item_snapshot から表示。
    snapshot = item.item_snapshot or {}
    return SuggestedOutfitItem(
        name=snapshot.get("name", ""),
        role=item.role,
        color=snapshot.get("color"),
        pattern=snapshot.get("pattern"),
        display_order=item.display_order,
        clothing_item=None,
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
        coordinate_image_url=outfit.coordinate_image_url,
        is_favorite=outfit.is_favorite,
        source=outfit.source,
        items=[
            _to_outfit_item_schema(item)
            for item in sorted(outfit.items, key=lambda item: item.display_order)
        ],
        created_at=outfit.created_at,
    )


def _items_loader():
    """outfit.items とその手持ち服（あれば）を eager load する options。"""
    return selectinload(Outfit.items).options(
        selectinload(OutfitItem.clothes).selectinload(Clothes.tpo_tags)
    )


async def _get_outfit_orm(
    db: AsyncSession, user_id: uuid.UUID, outfit_id: uuid.UUID
) -> Outfit | None:
    return await db.scalar(
        select(Outfit)
        .where(Outfit.id == outfit_id, Outfit.user_id == user_id)
        .options(_items_loader())
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
            .options(_items_loader())
            .order_by(Outfit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    return OutfitsListResponse(
        items=[_to_outfit_schema(outfit) for outfit in outfits],
        total=total,
    )


async def get_outfit(
    db: AsyncSession, user_id: uuid.UUID, outfit_id: uuid.UUID
) -> SuggestedOutfit | None:
    outfit = await _get_outfit_orm(db, user_id, outfit_id)
    if outfit is None:
        return None
    return _to_outfit_schema(outfit)


async def create_outfit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tpo: str,
    region_code: str,
    comment: str | None,
    is_favorite: bool,
    items: list[OutfitCreateItem],
) -> SuggestedOutfit:
    """提案コーデ（手持ち＋補完）を永続化する。

    clothes_id 付きアイテムはユーザー所有を検証し owned として保存、
    それ以外は item_snapshot を伴う suggested として保存する。
    """
    requested_clothes_ids = {it.clothes_id for it in items if it.clothes_id is not None}
    owned_by_id: dict[uuid.UUID, Clothes] = {}
    if requested_clothes_ids:
        rows = (
            await db.scalars(
                select(Clothes).where(
                    Clothes.user_id == user_id,
                    Clothes.id.in_(requested_clothes_ids),
                )
            )
        ).all()
        owned_by_id = {c.id: c for c in rows}
        not_owned = requested_clothes_ids - set(owned_by_id)
        if not_owned:
            raise OutfitItemNotOwnedError(not_owned)

    outfit = Outfit(
        user_id=user_id,
        tpo=tpo,
        region_code=region_code,
        weather_summary=None,
        comment=comment,
        is_favorite=is_favorite,
        source="llm",
    )
    db.add(outfit)
    await db.flush()

    for it in items:
        owned = owned_by_id.get(it.clothes_id) if it.clothes_id is not None else None
        if owned is not None:
            # owned も item_snapshot を DB 値で持たせる。服削除（clothes_id=SET NULL）
            # 後でも履歴として name/color/pattern を表示できるようにするため。
            db.add(
                OutfitItem(
                    outfit_id=outfit.id,
                    clothes_id=owned.id,
                    role=it.role,
                    source_type="owned",
                    item_snapshot={
                        "name": owned.name,
                        "color": owned.color,
                        "pattern": owned.pattern,
                    },
                    display_order=it.display_order,
                )
            )
        else:
            db.add(
                OutfitItem(
                    outfit_id=outfit.id,
                    clothes_id=None,
                    role=it.role,
                    source_type="suggested",
                    item_snapshot={
                        "name": it.name,
                        "color": it.color,
                        "pattern": it.pattern,
                    },
                    display_order=it.display_order,
                )
            )

    await db.commit()
    saved = await _get_outfit_orm(db, user_id, outfit.id)
    if saved is None:
        raise RuntimeError("failed to load just-created outfit")
    return _to_outfit_schema(saved)


async def update_outfit(
    db: AsyncSession,
    user_id: uuid.UUID,
    outfit_id: uuid.UUID,
    *,
    is_favorite: bool,
) -> SuggestedOutfit | None:
    outfit = await _get_outfit_orm(db, user_id, outfit_id)
    if outfit is None:
        return None
    outfit.is_favorite = is_favorite
    await db.commit()
    refreshed = await _get_outfit_orm(db, user_id, outfit_id)
    if refreshed is None:
        raise RuntimeError("failed to reload updated outfit")
    return _to_outfit_schema(refreshed)
