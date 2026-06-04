from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.dependencies import auth
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def stub_user_sync(monkeypatch) -> None:
    async def fake_get_or_create_user(db, *, user_id, email):
        return SimpleNamespace(id=user_id, email=email)

    monkeypatch.setattr(auth.user_crud, "get_or_create_user", fake_get_or_create_user)
