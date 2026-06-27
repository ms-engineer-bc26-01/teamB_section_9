from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import auth_bypass_misconfigured, settings
from app.main import app


def _fake_settings(*, app_env: str, bypass: bool) -> SimpleNamespace:
    return SimpleNamespace(APP_ENV=app_env, AUTH_BYPASS_ENABLED=bypass)


@pytest.mark.parametrize(
    ("app_env", "bypass", "expected"),
    [
        ("development", True, False),  # 開発でバイパス有効は許容
        ("development", False, False),
        ("production", False, False),
        ("production", True, True),  # 本番でバイパス有効は矛盾
        ("PRODUCTION", True, True),  # 大文字でも検知
        ("staging", True, True),
    ],
)
def test_auth_bypass_misconfigured(app_env: str, bypass: bool, expected: bool) -> None:
    assert (
        auth_bypass_misconfigured(_fake_settings(app_env=app_env, bypass=bypass))
        is expected
    )


def test_lifespan_fails_fast_on_misconfigured_auth_bypass(monkeypatch) -> None:
    # 本番なのにバイパス有効、という矛盾設定では起動時に fail-fast する。
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)

    with pytest.raises(RuntimeError, match="AUTH_BYPASS_ENABLED"):
        with TestClient(app):
            pass
