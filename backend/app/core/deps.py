from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        yield db
