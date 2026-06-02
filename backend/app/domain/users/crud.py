import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


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


async def update_default_region(
    db: AsyncSession,
    user_id: uuid.UUID,
    region_code: str,
) -> User:
    user = await get_user_or_404(db, user_id)
    user.default_region_code = region_code
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
