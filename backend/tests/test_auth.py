import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.routers import auth as auth_router
from app.core.config import settings
from app.dependencies import auth


def _auth_headers(token: str = "supabase-test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mock_supabase_user(monkeypatch, user_id: uuid.UUID | None = None) -> uuid.UUID:
    resolved_user_id = user_id or uuid.UUID("00000000-0000-0000-0000-000000000123")

    async def fake_verify_supabase_jwt(token: str) -> dict[str, object]:
        assert token == "supabase-test-token"
        return {
            "sub": str(resolved_user_id),
            "email": "jwt-user@example.com",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": "https://example.supabase.co/auth/v1",
            "exp": 9999999999,
        }

    monkeypatch.setattr(auth, "verify_supabase_jwt", fake_verify_supabase_jwt)
    return resolved_user_id


def _sample_user(user_id: uuid.UUID | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id or uuid.UUID("00000000-0000-0000-0000-000000000123"),
        email="jwt-user@example.com",
        display_name=None,
        default_region_code=None,
        secondary_region_code=None,
        subscription_status="free",
        stripe_customer_id=None,
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )


def test_get_me_returns_current_user_profile(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    expected_user_id = _mock_supabase_user(monkeypatch)
    captured: dict[str, object] = {}

    async def fake_get_or_create_user(db, *, user_id, email):
        captured["user_id"] = user_id
        captured["email"] = email
        return SimpleNamespace(id=user_id, email=email)

    async def fake_get_user_or_404(db, user_id):
        assert user_id == expected_user_id
        return _sample_user(user_id)

    monkeypatch.setattr(auth.user_crud, "get_or_create_user", fake_get_or_create_user)
    monkeypatch.setattr(auth_router.crud, "get_user_or_404", fake_get_user_or_404)

    response = client.get("/api/v1/auth/me", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "id": str(expected_user_id),
        "email": "jwt-user@example.com",
        "display_name": None,
        "default_region_code": None,
        "secondary_region_code": None,
        "subscription_status": "free",
        "stripe_customer_id": None,
        "created_at": "2026-06-01T00:00:00Z",
    }
    assert captured == {
        "user_id": expected_user_id,
        "email": "jwt-user@example.com",
    }


def test_replace_me_updates_profile(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    expected_user_id = _mock_supabase_user(monkeypatch)

    async def fake_update_user_profile(db, user_id, **kwargs):
        assert user_id == expected_user_id
        assert kwargs == {
            "display_name": "Miwa",
            "default_region_code": "13_01",
            "secondary_region_code": "13_02",
        }
        user = _sample_user(user_id)
        user.display_name = "Miwa"
        user.default_region_code = "13_01"
        user.secondary_region_code = "13_02"
        return user

    monkeypatch.setattr(
        auth_router.crud,
        "update_user_profile",
        fake_update_user_profile,
    )

    response = client.put(
        "/api/v1/auth/me",
        json={
            "display_name": "Miwa",
            "default_region_code": "13_01",
            "secondary_region_code": "13_02",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Miwa"
    assert response.json()["default_region_code"] == "13_01"
    assert response.json()["secondary_region_code"] == "13_02"


def test_patch_me_updates_only_display_name(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    expected_user_id = _mock_supabase_user(monkeypatch)

    async def fake_get_user_or_404(db, user_id):
        assert user_id == expected_user_id
        user = _sample_user(user_id)
        user.default_region_code = "13_01"
        user.secondary_region_code = "13_02"
        return user

    async def fake_update_user_profile(db, user_id, **kwargs):
        assert user_id == expected_user_id
        assert kwargs == {"display_name": "Renamed"}
        user = _sample_user(user_id)
        user.display_name = "Renamed"
        user.default_region_code = "13_01"
        user.secondary_region_code = "13_02"
        return user

    monkeypatch.setattr(auth_router.crud, "get_user_or_404", fake_get_user_or_404)
    monkeypatch.setattr(
        auth_router.crud,
        "update_user_profile",
        fake_update_user_profile,
    )

    response = client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Renamed"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Renamed"


def test_patch_me_returns_400_for_duplicate_region_codes(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    expected_user_id = _mock_supabase_user(monkeypatch)

    async def fake_get_user_or_404(db, user_id):
        assert user_id == expected_user_id
        user = _sample_user(user_id)
        user.default_region_code = "13_01"
        user.secondary_region_code = "13_02"
        return user

    async def fail_if_called(db, user_id, **kwargs):
        raise AssertionError("update_user_profile should not be called")

    monkeypatch.setattr(auth_router.crud, "get_user_or_404", fake_get_user_or_404)
    monkeypatch.setattr(auth_router.crud, "update_user_profile", fail_if_called)

    response = client.patch(
        "/api/v1/auth/me",
        json={"secondary_region_code": "13_01"},
        headers=_auth_headers(),
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "secondary region must be different from default region"
    )


async def test_get_current_user_returns_13_01_in_bypass_mode(monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    current_user = await auth.get_current_user(token=None)

    assert current_user.id == uuid.UUID("00000000-0000-0000-0000-000000000001")
    assert current_user.email == "test@example.com"
    assert current_user.default_region_code == "13_01"
    assert current_user.secondary_region_code == "13_02"
