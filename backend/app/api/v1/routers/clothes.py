import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.clothes import (
    ClothesListResponse,
    ClothingCreateRequest,
    ClothingItem,
    ClothingUpdateRequest,
)
from app.core.deps import CurrentUser, get_current_user, get_db
from app.domain.clothes import crud

router = APIRouter(prefix="/clothes", tags=["Clothes"])


DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("", response_model=ClothesListResponse)
async def list_clothes(
    db: DbSession,
    current_user: AuthenticatedUser,
    category: str | None = None,
    season: str | None = None,
    tpo: str | None = None,
    is_favorite: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ClothesListResponse:
    return await crud.list_clothes(
        db,
        current_user.id,
        category=category,
        season=season,
        tpo=tpo,
        is_favorite=is_favorite,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ClothingItem, status_code=status.HTTP_201_CREATED)
async def create_clothing(
    payload: ClothingCreateRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.create_clothing(db, current_user.id, payload)


@router.get("/{clothing_id}", response_model=ClothingItem)
async def get_clothing(
    clothing_id: uuid.UUID,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.get_clothing(db, current_user.id, clothing_id)


@router.put("/{clothing_id}", response_model=ClothingItem)
async def replace_clothing(
    clothing_id: uuid.UUID,
    payload: ClothingUpdateRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.update_clothing(db, current_user.id, clothing_id, payload)


@router.patch("/{clothing_id}", response_model=ClothingItem)
async def patch_clothing(
    clothing_id: uuid.UUID,
    payload: ClothingUpdateRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.update_clothing(db, current_user.id, clothing_id, payload)


@router.delete("/{clothing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clothing(
    clothing_id: uuid.UUID,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> Response:
    await crud.delete_clothing(db, current_user.id, clothing_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
