import asyncio
import time
from typing import Any

import httpx
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWK

from app.core.config import settings

ALLOWED_JWT_ALGORITHMS = ("RS256", "ES256", "EdDSA")

_jwks_cache: dict[str, Any] | None = None
_jwks_cache_expires_at = 0.0
_jwks_lock = asyncio.Lock()


class SupabaseJWTError(Exception):
    pass


def _supabase_auth_base_url() -> str:
    if not settings.SUPABASE_URL:
        raise RuntimeError("Supabase authentication is not configured")
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"


def _supabase_jwks_url() -> str:
    return f"{_supabase_auth_base_url()}/.well-known/jwks.json"


def _supabase_issuer() -> str:
    return _supabase_auth_base_url()


async def _fetch_jwks() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(_supabase_jwks_url())

    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
        raise RuntimeError("Invalid JWKS response")
    return payload


async def _get_cached_jwks(*, force_refresh: bool = False) -> dict[str, Any]:
    global _jwks_cache
    global _jwks_cache_expires_at

    now = time.monotonic()
    if not force_refresh and _jwks_cache is not None and now < _jwks_cache_expires_at:
        return _jwks_cache

    async with _jwks_lock:
        now = time.monotonic()
        if (
            not force_refresh
            and _jwks_cache is not None
            and now < _jwks_cache_expires_at
        ):
            return _jwks_cache

        jwks = await _fetch_jwks()
        _jwks_cache = jwks
        _jwks_cache_expires_at = now + settings.SUPABASE_JWKS_CACHE_TTL_SECONDS
        return jwks


def _find_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        return None

    for key in keys:
        if isinstance(key, dict) and key.get("kid") == kid:
            return key
    return None


async def _get_signing_jwk(token: str) -> PyJWK:
    try:
        header = jwt.get_unverified_header(token)
    except InvalidTokenError as exc:
        raise SupabaseJWTError("Invalid authentication credentials") from exc

    kid = header.get("kid")
    algorithm = header.get("alg")
    if not isinstance(kid, str) or not kid:
        raise SupabaseJWTError("Invalid authentication credentials")
    if algorithm not in ALLOWED_JWT_ALGORITHMS:
        raise SupabaseJWTError("Invalid authentication credentials")

    jwks = await _get_cached_jwks()
    jwk_data = _find_jwk(jwks, kid)
    if jwk_data is None:
        jwks = await _get_cached_jwks(force_refresh=True)
        jwk_data = _find_jwk(jwks, kid)
    if jwk_data is None:
        raise SupabaseJWTError("Invalid authentication credentials")

    try:
        return PyJWK.from_dict(jwk_data)
    except Exception as exc:
        raise SupabaseJWTError("Invalid authentication credentials") from exc


async def verify_supabase_jwt(token: str) -> dict[str, Any]:
    try:
        signing_jwk = await _get_signing_jwk(token)
    except RuntimeError as exc:
        raise SupabaseJWTError("Supabase authentication is not configured") from exc

    try:
        payload = jwt.decode(
            token,
            signing_jwk.key,
            algorithms=[signing_jwk.algorithm_name],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=_supabase_issuer(),
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except ExpiredSignatureError as exc:
        raise SupabaseJWTError("Invalid authentication credentials") from exc
    except InvalidTokenError as exc:
        raise SupabaseJWTError("Invalid authentication credentials") from exc

    email = payload.get("email")
    if not isinstance(email, str) or not email:
        raise SupabaseJWTError("Invalid authentication credentials")

    return payload


def clear_jwks_cache() -> None:
    global _jwks_cache
    global _jwks_cache_expires_at

    _jwks_cache = None
    _jwks_cache_expires_at = 0.0
