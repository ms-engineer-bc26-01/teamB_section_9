from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import UpdateDefaultRegionRequest, UserResponse
from app.constants.regions import get_region
from app.core.deps import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.users import crud

router = APIRouter(prefix="/auth", tags=["Auth"])


DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: DbSession,
    current_user: AuthenticatedUser,
) -> UserResponse:
    return await crud.get_user_or_404(db, current_user.id)


@router.put("/me/default-region", response_model=UserResponse)
async def update_default_region(
    payload: UpdateDefaultRegionRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> UserResponse:
    if get_region(payload.region_code) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )

    return await crud.update_default_region(db, current_user.id, payload.region_code)
