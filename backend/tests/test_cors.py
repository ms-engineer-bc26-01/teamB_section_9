from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import build_cors_kwargs

# app の CORS 設定は import 時に `app.add_middleware(... build_cors_kwargs(settings))` で
# 確定する（その時点の APP_ENV で dev/prod を分岐。LAN regex 文字列自体は定数）。
# そのため client 経由の実リクエスト検証は development 時のみ有効化し、production では
# スキップする（dev/prod の分岐ロジックは build_cors_kwargs の単体テストで担保）。
_dev_only = pytest.mark.skipif(
    settings.APP_ENV.lower() != "development",
    reason="CORS LAN regex is only active in development",
)


def test_cors_preflight_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def _settings(app_env: str) -> SimpleNamespace:
    return SimpleNamespace(
        APP_ENV=app_env,
        BACKEND_CORS_ORIGINS=["http://localhost:3000"],
    )


def test_build_cors_kwargs_allows_lan_regex_in_development() -> None:
    kwargs = build_cors_kwargs(_settings("development"))
    assert "allow_origin_regex" in kwargs
    assert kwargs["allow_origins"] == ["http://localhost:3000"]


def test_build_cors_kwargs_no_lan_regex_in_production() -> None:
    kwargs = build_cors_kwargs(_settings("production"))
    assert "allow_origin_regex" not in kwargs


def _preflight_allowed_origin(client: TestClient, origin: str) -> str | None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    return response.headers.get("access-control-allow-origin")


@_dev_only
def test_lan_phone_origin_is_allowed_in_dev(client: TestClient) -> None:
    origin = "http://192.168.10.50:3000"
    assert _preflight_allowed_origin(client, origin) == origin


@_dev_only
def test_public_ip_origin_is_not_allowed(client: TestClient) -> None:
    # private 帯でない IP は LAN regex に一致しないため許可されない。
    assert _preflight_allowed_origin(client, "http://203.0.113.10:3000") is None


@_dev_only
def test_wrong_port_lan_origin_is_not_allowed(client: TestClient) -> None:
    # ポート 3000 以外は許可しない。
    assert _preflight_allowed_origin(client, "http://192.168.10.50:9999") is None
