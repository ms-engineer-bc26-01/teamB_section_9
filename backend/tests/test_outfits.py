from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIError

from app.core.config import settings
from app.domain.outfits.service import OutfitService, OutfitSuggestionError


@pytest.mark.asyncio
async def test_outfit_service_uses_prompt_template_independent_of_cwd(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, str] = {}

    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return "generated-coordinate"

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )
    monkeypatch.chdir(tmp_path)

    service = OutfitService()
    result = await service.suggest(
        clothes=["white shirt", "black pants"],
        weather="sunny",
    )

    assert result == "generated-coordinate"
    assert "white shirt, black pants" in captured["prompt"]
    assert "sunny" in captured["prompt"]


@pytest.mark.asyncio
async def test_outfit_service_wraps_llm_api_errors(monkeypatch) -> None:
    class FakeLLMClient:
        async def generate(self, prompt: str) -> str:
            del prompt
            raise APIError(
                "upstream failure",
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                body=None,
            )

    monkeypatch.setattr(
        "app.domain.outfits.service.get_llm_client", lambda: FakeLLMClient()
    )

    service = OutfitService()

    with pytest.raises(OutfitSuggestionError) as exc_info:
        await service.suggest(
            clothes=["white shirt"],
            weather="sunny",
        )

    assert str(exc_info.value) == "failed to generate outfit suggestion"
    assert isinstance(exc_info.value.__cause__, APIError)


def test_suggest_outfit_requires_authentication(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"clothes": ["white shirt"], "weather": "sunny"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_suggest_outfit_returns_bad_gateway_on_llm_failure(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeOutfitService:
        async def suggest(self, clothes: list[str], weather: str) -> str:
            del clothes, weather
            raise OutfitSuggestionError("failed to generate outfit suggestion")

    monkeypatch.setattr(settings, "AUTH_BYPASS_ENABLED", True)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr("app.api.v1.routers.outfits.OutfitService", FakeOutfitService)

    response = client.post(
        "/api/v1/outfits/suggest",
        json={"clothes": ["white shirt"], "weather": "sunny"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "failed to generate outfit suggestion"
