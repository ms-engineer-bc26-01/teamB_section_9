from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.outfits.service import OutfitService


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
