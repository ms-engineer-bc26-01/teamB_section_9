from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _engine_kwargs() -> dict:
    database_url = make_url(settings.DATABASE_URL)
    if (
        database_url.get_backend_name() == "postgresql"
        and database_url.get_driver_name() == "psycopg"
        and (database_url.host or "").endswith(".pooler.supabase.com")
    ):
        return {"connect_args": {"prepare_threshold": None}}
    return {}


engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs())

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
