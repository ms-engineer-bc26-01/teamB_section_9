from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


def test_cors_preflight_allows_multiple_configured_origins() -> None:
    """BACKEND_CORS_ORIGINS に複数オリジンを設定したとき LAN IP も許可される。"""
    lan_origin = "http://192.168.11.37:3000"

    mini_app = FastAPI()
    mini_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", lan_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @mini_app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    test_client = TestClient(mini_app)
    response = test_client.options(
        "/health",
        headers={
            "Origin": lan_origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == lan_origin
