from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import (
    PatchUserProfileRequest,
    ReplaceUserProfileRequest,
    UserResponse,
)
from app.constants.regions import get_region
from app.core.deps import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.domain.users import crud

router = APIRouter(prefix="/auth", tags=["Auth"])


DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


def _validate_region_code(region_code: str | None) -> None:
    if region_code is not None and get_region(region_code) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid region_code",
        )


def _validate_region_pair(
    default_region_code: str | None,
    secondary_region_code: str | None,
) -> None:
    if (
        default_region_code is not None
        and secondary_region_code is not None
        and default_region_code == secondary_region_code
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="secondary region must be different from default region",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: DbSession,
    current_user: AuthenticatedUser,
) -> UserResponse:
    user = await crud.get_user_or_404(db, current_user.id)
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def replace_me(
    payload: ReplaceUserProfileRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> UserResponse:
    _validate_region_code(payload.default_region_code)
    _validate_region_code(payload.secondary_region_code)
    _validate_region_pair(
        payload.default_region_code,
        payload.secondary_region_code,
    )

    user = await crud.update_user_profile(
        db,
        current_user.id,
        display_name=payload.display_name,
        default_region_code=payload.default_region_code,
        secondary_region_code=payload.secondary_region_code,
    )
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    payload: PatchUserProfileRequest,
    db: DbSession,
    current_user: AuthenticatedUser,
) -> UserResponse:
    current_profile = await crud.get_user_or_404(db, current_user.id)

    default_region_code = (
        payload.default_region_code
        if "default_region_code" in payload.model_fields_set
        else current_profile.default_region_code
    )
    secondary_region_code = (
        payload.secondary_region_code
        if "secondary_region_code" in payload.model_fields_set
        else current_profile.secondary_region_code
    )

    if "default_region_code" in payload.model_fields_set:
        _validate_region_code(payload.default_region_code)
    if "secondary_region_code" in payload.model_fields_set:
        _validate_region_code(payload.secondary_region_code)
    _validate_region_pair(default_region_code, secondary_region_code)

    user = await crud.update_user_profile(
        db,
        current_user.id,
        **payload.model_dump(exclude_unset=True),
    )
    return UserResponse.model_validate(user)
