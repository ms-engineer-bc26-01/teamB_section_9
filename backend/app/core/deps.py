import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class CurrentUser:
    id: uuid.UUID
    email: str


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        yield db


def get_current_user() -> CurrentUser:
    return CurrentUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
    )
