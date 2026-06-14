import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.config import settings
from app.dependencies import auth
from app.domain.clothes import crud


def _sample_item(clothing_id: uuid.UUID | None = None) -> dict:
    item_id = clothing_id or uuid.uuid4()
    now = datetime(2026, 5, 29, 0, 0, tzinfo=UTC)
    return {
        "id": str(item_id),
        "user_id": "00000000-0000-0000-0000-000000000001",
        "name": "白シャツ",
        "category": "tops",
        "color": "white",
        "pattern": "solid",
        "size": "M",
        "season": ["spring", "autumn"],
        "tpo_tags": ["casual"],
        "image_url": "https://example.com/shirt.jpg",
        "thumbnail_url": None,
        "memo": "test memo",
        "is_favorite": False,
        "wear_count": 0,
        "last_worn_at": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


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


def test_list_clothes_returns_items(client: TestClient, monkeypatch) -> None:
    captured: dict[str, object] = {}
    expected_user_id = _mock_supabase_user(monkeypatch)

    async def fake_list_clothes(db, user_id, **filters):
        captured["user_id"] = user_id
        captured.update(filters)
        return {"items": [_sample_item()], "total": 1}

    monkeypatch.setattr(crud, "list_clothes", fake_list_clothes)

    response = client.get(
        "/api/v1/clothes",
        params={"category": "tops", "season": "spring", "limit": 10, "offset": 5},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "白シャツ"
    assert captured["user_id"] == expected_user_id
    assert captured["category"] == "tops"
    assert captured["season"] == "spring"
    assert captured["limit"] == 10
    assert captured["offset"] == 5


def test_create_clothing_returns_created_item(client: TestClient, monkeypatch) -> None:
    _mock_supabase_user(monkeypatch)

    async def fake_create_clothing(db, user_id, payload):
        item = _sample_item()
        item["name"] = payload.name
        item["category"] = payload.category
        item["tpo_tags"] = payload.tpo_tags
        return item

    monkeypatch.setattr(crud, "create_clothing", fake_create_clothing)

    response = client.post(
        "/api/v1/clothes",
        json={
            "name": "黒パンツ",
            "category": "bottoms",
            "season": ["winter"],
            "tpo_tags": ["business"],
            "image_url": "https://example.com/pants.jpg",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "黒パンツ"
    assert body["category"] == "bottoms"
    assert body["tpo_tags"] == ["business"]


def test_create_clothing_allows_missing_image_url(
    client: TestClient,
    monkeypatch,
) -> None:
    _mock_supabase_user(monkeypatch)

    async def fake_create_clothing(db, user_id, payload):
        item = _sample_item()
        item["name"] = payload.name
        item["category"] = payload.category
        item["tpo_tags"] = payload.tpo_tags
        item["image_url"] = payload.image_url
        return item

    monkeypatch.setattr(crud, "create_clothing", fake_create_clothing)

    response = client.post(
        "/api/v1/clothes",
        json={
            "name": "画像なしシャツ",
            "category": "tops",
            "season": ["spring"],
            "tpo_tags": ["casual"],
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "画像なしシャツ"
    assert body["category"] == "tops"
    assert body["tpo_tags"] == ["casual"]
    assert body["image_url"] is None


def test_get_clothing_returns_item(client: TestClient, monkeypatch) -> None:
    clothing_id = uuid.uuid4()
    _mock_supabase_user(monkeypatch)

    async def fake_get_clothing(db, user_id, requested_id):
        assert requested_id == clothing_id
        return _sample_item(clothing_id)

    monkeypatch.setattr(crud, "get_clothing", fake_get_clothing)

    response = client.get(f"/api/v1/clothes/{clothing_id}", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json()["id"] == str(clothing_id)


def test_patch_clothing_returns_updated_item(client: TestClient, monkeypatch) -> None:
    clothing_id = uuid.uuid4()
    _mock_supabase_user(monkeypatch)

    async def fake_update_clothing(db, user_id, requested_id, payload):
        assert requested_id == clothing_id
        item = _sample_item(clothing_id)
        item["is_favorite"] = payload.is_favorite
        return item

    monkeypatch.setattr(crud, "update_clothing", fake_update_clothing)

    response = client.patch(
        f"/api/v1/clothes/{clothing_id}",
        json={"is_favorite": True},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is True


def test_delete_clothing_returns_no_content(client: TestClient, monkeypatch) -> None:
    clothing_id = uuid.uuid4()
    captured: dict[str, object] = {}
    _mock_supabase_user(monkeypatch)

    async def fake_delete_clothing(db, user_id, requested_id):
        captured["clothing_id"] = requested_id

    monkeypatch.setattr(crud, "delete_clothing", fake_delete_clothing)

    response = client.delete(f"/api/v1/clothes/{clothing_id}", headers=_auth_headers())

    assert response.status_code == 204
    assert response.content == b""
    assert captured["clothing_id"] == clothing_id


def test_clothes_returns_401_without_auth_when_bypass_disabled(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    response = client.get("/api/v1/clothes")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_clothes_uses_mock_user_when_bypass_enabled(
    client: TestClient,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    async def fake_list_clothes(db, user_id, **filters):
        captured["user_id"] = user_id
        captured.update(filters)
        return {"items": [], "total": 0}

    monkeypatch.setattr(crud, "list_clothes", fake_list_clothes)

    response = client.get("/api/v1/clothes")

    assert response.status_code == 200
    assert captured["user_id"] == uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_clothes_returns_401_when_supabase_rejects_token(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_verify_supabase_jwt(token: str) -> dict[str, object]:
        raise auth.SupabaseJWTError("Invalid authentication credentials")

    monkeypatch.setattr(auth, "verify_supabase_jwt", fake_verify_supabase_jwt)

    response = client.get("/api/v1/clothes", headers=_auth_headers())

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"
