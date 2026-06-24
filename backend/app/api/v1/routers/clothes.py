import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.clothes import (
    ClothesListResponse,
    ClothingCreateRequest,
    ClothingItem,
    ClothingUpdateRequest,
    ClothingUploadUrlRequest,
    UploadUrlResponse,
)
from app.core.deps import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.clothes import crud
from app.services import storage_client

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


@router.get("/{clothes_id}", response_model=ClothingItem)
async def get_clothing(
    clothes_id: uuid.UUID,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.get_clothing(db, current_user.id, clothes_id)


@router.put("/{clothes_id}", response_model=ClothingItem)
async def replace_clothing(
    clothes_id: uuid.UUID,
    payload: ClothingUpdateRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.update_clothing(db, current_user.id, clothes_id, payload)


@router.patch("/{clothes_id}", response_model=ClothingItem)
async def patch_clothing(
    clothes_id: uuid.UUID,
    payload: ClothingUpdateRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> ClothingItem:
    return await crud.update_clothing(db, current_user.id, clothes_id, payload)


@router.delete("/{clothes_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clothing(
    clothes_id: uuid.UUID,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> Response:
    await crud.delete_clothing(db, current_user.id, clothes_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/upload-url", response_model=UploadUrlResponse)
async def create_clothing_upload_url(
    payload: ClothingUploadUrlRequest,
    current_user: AuthenticatedUser,
) -> UploadUrlResponse:
    try:
        upload_url, storage_path = await storage_client.create_signed_upload_url(
            user_id=current_user.id,
            filename=payload.filename,
            content_type=payload.content_type,
        )
    except storage_client.StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to create upload url",
        ) from exc

    return UploadUrlResponse(
        upload_url=upload_url,
        storage_path=storage_path,
        image_url=storage_client.build_public_url(storage_path),
    )
