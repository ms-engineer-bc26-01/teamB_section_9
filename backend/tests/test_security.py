import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import security
from app.core.config import settings


def _build_rsa_material() -> tuple[object, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk["kid"] = "test-key"
    public_jwk["alg"] = "RS256"
    public_jwk["use"] = "sig"
    return private_key, public_jwk


def _build_token(private_key: object, **overrides: object) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000123",
        "email": "jwt-user@example.com",
        "aud": settings.SUPABASE_JWT_AUDIENCE,
        "iss": "https://example.supabase.co/auth/v1",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    payload.update(overrides)
    return jwt.encode(
        payload, private_key, algorithm="RS256", headers={"kid": "test-key"}
    )


@pytest.mark.asyncio
async def test_verify_supabase_jwt_accepts_valid_token(monkeypatch) -> None:
    private_key, public_jwk = _build_rsa_material()
    security.clear_jwks_cache()
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")

    async def fake_fetch_jwks() -> dict[str, object]:
        return {"keys": [public_jwk]}

    monkeypatch.setattr(security, "_fetch_jwks", fake_fetch_jwks)

    payload = await security.verify_supabase_jwt(_build_token(private_key))

    assert payload["sub"] == "00000000-0000-0000-0000-000000000123"
    assert payload["email"] == "jwt-user@example.com"


@pytest.mark.asyncio
async def test_verify_supabase_jwt_rejects_invalid_audience(monkeypatch) -> None:
    private_key, public_jwk = _build_rsa_material()
    security.clear_jwks_cache()
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")

    async def fake_fetch_jwks() -> dict[str, object]:
        return {"keys": [public_jwk]}

    monkeypatch.setattr(security, "_fetch_jwks", fake_fetch_jwks)

    with pytest.raises(security.SupabaseJWTError):
        await security.verify_supabase_jwt(_build_token(private_key, aud="wrong"))


@pytest.mark.asyncio
async def test_verify_supabase_jwt_rejects_invalid_issuer(monkeypatch) -> None:
    private_key, public_jwk = _build_rsa_material()
    security.clear_jwks_cache()
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")

    async def fake_fetch_jwks() -> dict[str, object]:
        return {"keys": [public_jwk]}

    monkeypatch.setattr(security, "_fetch_jwks", fake_fetch_jwks)

    with pytest.raises(security.SupabaseJWTError):
        await security.verify_supabase_jwt(
            _build_token(private_key, iss="https://wrong.example/auth/v1")
        )


@pytest.mark.asyncio
async def test_verify_supabase_jwt_rejects_missing_email(monkeypatch) -> None:
    private_key, public_jwk = _build_rsa_material()
    security.clear_jwks_cache()
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")

    async def fake_fetch_jwks() -> dict[str, object]:
        return {"keys": [public_jwk]}

    monkeypatch.setattr(security, "_fetch_jwks", fake_fetch_jwks)

    with pytest.raises(security.SupabaseJWTError):
        await security.verify_supabase_jwt(_build_token(private_key, email=None))
