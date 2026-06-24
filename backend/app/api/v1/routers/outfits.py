import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.outfits import (
    OutfitCreateRequest,
    OutfitsListResponse,
    OutfitSuggestRequest,
    OutfitSuggestResponse,
    OutfitUpdateRequest,
    SuggestedOutfit,
    SuggestOutfit,
    SuggestOutfitItem,
)
from app.constants.regions import get_region
from app.core.deps import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.outfits import crud as outfits_crud
from app.domain.outfits import orchestration as outfits_orchestration
from app.domain.outfits.crud import OutfitItemNotOwnedError
from app.domain.outfits.image_service import generate_and_store_coordinate_image
from app.domain.outfits.service import OutfitSuggestionError

router = APIRouter(prefix="/outfits", tags=["Outfits"])


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=OutfitsListResponse)
async def list_outfits(
    current_user: AuthenticatedUser,
    db: DbSession,
    is_favorite: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OutfitsListResponse:
    return await outfits_crud.list_outfits(
        db,
        current_user.id,
        is_favorite=is_favorite,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=SuggestedOutfit, status_code=status.HTTP_201_CREATED)
async def create_outfit(
    request: OutfitCreateRequest,
    current_user: AuthenticatedUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> SuggestedOutfit:
    """提案コーデ（手持ち＋補完アイテム）を履歴として保存する。

    コラージュ画像の生成・Storage アップロードは時間がかかる（最大数十秒）ため、
    保存 API のレスポンスをブロックしない。コーデを保存して即時 201 を返し
    （coordinate_image_url=null）、画像生成は背景タスクへ切り出して
    完了後に URL を反映する。
    """
    region = get_region(request.region_code)
    if region is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )

    try:
        saved = await outfits_crud.create_outfit(
            db,
            user_id=current_user.id,
            tpo=request.tpo,
            region_code=request.region_code,
            comment=request.comment,
            is_favorite=request.is_favorite,
            items=request.items,
        )
    except OutfitItemNotOwnedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="clothes_id contains items not owned by the user",
        ) from exc

    # コラージュ画像生成は best-effort かつ低速なため背景タスクで実行する。
    # saved は ORM ではなく Pydantic スキーマなので、
    # セッション境界をまたいで安全に渡せる。
    background_tasks.add_task(
        generate_and_store_coordinate_image,
        outfit_id=saved.id,
        user_id=current_user.id,
        comment=saved.comment,
        items=saved.items,
    )

    return saved


@router.get("/{outfit_id}", response_model=SuggestedOutfit)
async def get_outfit(
    outfit_id: uuid.UUID,
    current_user: AuthenticatedUser,
    db: DbSession,
) -> SuggestedOutfit:
    outfit = await outfits_crud.get_outfit(db, current_user.id, outfit_id)
    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="outfit not found",
        )
    return outfit


@router.patch("/{outfit_id}", response_model=SuggestedOutfit)
async def update_outfit(
    outfit_id: uuid.UUID,
    request: OutfitUpdateRequest,
    current_user: AuthenticatedUser,
    db: DbSession,
) -> SuggestedOutfit:
    outfit = await outfits_crud.update_outfit(
        db,
        current_user.id,
        outfit_id,
        is_favorite=request.is_favorite,
    )
    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="outfit not found",
        )
    return outfit


@router.post(
    "/suggest",
    response_model=OutfitSuggestResponse,
)
async def suggest_outfit(
    request: OutfitSuggestRequest,
    current_user: AuthenticatedUser,
    db: DbSession,
):
    try:
        plan = await outfits_orchestration.build_outfit_suggestion_plan(
            db,
            user_id=current_user.id,
            default_region_code=current_user.default_region_code,
            tpo=request.tpo,
            region_code=request.region_code,
            clothing_ids=request.clothing_ids,
            exclude_clothing_ids=request.exclude_clothing_ids,
        )
    except outfits_orchestration.InvalidRegionCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        ) from exc
    except outfits_orchestration.OutfitWeatherError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to fetch weather forecast",
        ) from exc
    except OutfitSuggestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to generate outfit suggestion",
        ) from exc

    outfit_id = uuid.uuid4()
    created_at = datetime.now(UTC)

    return OutfitSuggestResponse(
        outfits=[
            SuggestOutfit(
                id=outfit_id,
                user_id=current_user.id,
                tpo=plan.tpo,
                region_code=plan.region_code,
                comment=plan.comment,
                is_favorite=False,
                items=[
                    SuggestOutfitItem(
                        name=item.name,
                        role=item.role,
                        color=item.color,
                        pattern=item.pattern,
                        display_order=item.display_order,
                        clothing_item=item.clothing_item,
                    )
                    for item in plan.items
                ],
                created_at=created_at,
            )
        ],
    )
