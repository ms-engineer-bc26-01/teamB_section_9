import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import SupabaseJWTError, verify_supabase_jwt
from app.db.session import SessionLocal
from app.domain.users import crud as user_crud


@dataclass(slots=True)
class CurrentUser:
    id: uuid.UUID
    email: str
    default_region_code: str | None = None
    secondary_region_code: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def _mock_current_user() -> CurrentUser:
    return CurrentUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
        default_region_code="13_01",
        secondary_region_code="13_02",
    )


def _is_auth_bypass_enabled() -> bool:
    return settings.APP_ENV.lower() == "development" and settings.AUTH_BYPASS_ENABLED


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> CurrentUser:
    if _is_auth_bypass_enabled():
        return _mock_current_user()

    if token is None:
        raise _unauthorized()

    try:
        payload = await verify_supabase_jwt(token)
    except SupabaseJWTError as exc:
        raise _unauthorized(str(exc)) from exc

    raw_user_id = payload.get("sub")
    email = payload.get("email")
    if not isinstance(raw_user_id, str) or not isinstance(email, str):
        raise _unauthorized("Invalid authentication credentials")

    try:
        user_id = uuid.UUID(raw_user_id)
    except ValueError as exc:
        raise _unauthorized("Invalid authentication credentials") from exc

    async with SessionLocal() as db:
        user = await user_crud.get_or_create_user(db, user_id=user_id, email=email)

    email = user.email
    return CurrentUser(
        id=user_id,
        email=email,
        default_region_code=getattr(user, "default_region_code", None),
        secondary_region_code=getattr(user, "secondary_region_code", None),
    )
