import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

_UNSET: Any = object()


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.scalar(select(User).where(User.id == user_id))


async def get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found",
        )
    return user


async def get_or_create_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    email: str,
) -> User:
    user = await get_user(db, user_id)
    if user is None:
        user = User(id=user_id, email=email)
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            user = await get_user(db, user_id)
            if user is None:
                raise
            return user
        await db.refresh(user)
        return user

    if user.email != email:
        user.email = email
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    display_name: str | None | object = _UNSET,
    default_region_code: str | None | object = _UNSET,
    secondary_region_code: str | None | object = _UNSET,
) -> User:
    user = await get_user_or_404(db, user_id)

    if display_name is not _UNSET:
        user.display_name = display_name
    if default_region_code is not _UNSET:
        user.default_region_code = default_region_code
    if secondary_region_code is not _UNSET:
        user.secondary_region_code = secondary_region_code

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
