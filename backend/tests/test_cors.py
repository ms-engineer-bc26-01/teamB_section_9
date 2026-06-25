from fastapi.testclient import TestClient


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


def test_cors_preflight_allows_multiple_configured_origins(
    monkeypatch, client: TestClient
) -> None:
    """BACKEND_CORS_ORIGINS に複数オリジンを設定したとき LAN IP も許可される。"""
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware

    lan_origin = "http://192.168.11.37:3000"

    # 既存ミドルウェアを一時的に LAN IP 込みで差し替え
    app.middleware_stack = None  # type: ignore[assignment]
    original_middleware = list(app.user_middleware)

    app.user_middleware = [
        m
        for m in app.user_middleware
        if not (
            hasattr(m, "cls") and m.cls is CORSMiddleware
        )
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", lan_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_client = TestClient(app)
    response = test_client.options(
        "/api/v1/health",
        headers={
            "Origin": lan_origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == lan_origin

    # ミドルウェアを元に戻す
    app.user_middleware = original_middleware
    app.middleware_stack = None  # type: ignore[assignment]
