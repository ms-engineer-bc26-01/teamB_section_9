import uuid
from unittest.mock import AsyncMock, Mock

from sqlalchemy.exc import IntegrityError

from app.db.models.user import User
from app.domain.users import crud
from app.domain.users.crud import get_or_create_user


async def test_get_or_create_user_recovers_from_integrity_error(monkeypatch) -> None:
    user_id = uuid.uuid4()
    existing_user = User(id=user_id, email="jwt-user@example.com")
    db = AsyncMock()
    db.add = Mock()
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate key"))

    get_user_calls = 0

    async def fake_get_user(session, requested_user_id):
        nonlocal get_user_calls
        get_user_calls += 1
        assert session is db
        assert requested_user_id == user_id
        if get_user_calls == 1:
            return None
        return existing_user

    monkeypatch.setattr(crud, "get_user", fake_get_user)

    user = await get_or_create_user(
        db,
        user_id=user_id,
        email="jwt-user@example.com",
    )

    assert user is existing_user
    assert get_user_calls == 2
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


async def test_list_users_orders_and_paginates(monkeypatch) -> None:
    db = AsyncMock()
    expected_users = [
        User(id=uuid.uuid4(), email="a@example.com"),
        User(id=uuid.uuid4(), email="b@example.com"),
    ]

    scalar_result = Mock()
    scalar_result.all.return_value = expected_users
    db.scalars.return_value = scalar_result

    users = await crud.list_users(db, limit=2, offset=3)

    assert users == expected_users
    db.scalars.assert_awaited_once()
