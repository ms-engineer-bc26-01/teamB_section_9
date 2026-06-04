import pytest

from app.core.config import settings
from app.services import llm_client


def test_get_llm_client_returns_openai_client_for_openai_provider(monkeypatch) -> None:
    class FakeOpenAIClient:
        pass

    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")

    from app.services import openai_client

    monkeypatch.setattr(openai_client, "OpenAIClient", FakeOpenAIClient)

    client = llm_client.get_llm_client()

    assert isinstance(client, FakeOpenAIClient)


def test_get_llm_client_raises_for_unsupported_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "claude")

    with pytest.raises(ValueError, match="Unsupported LLM provider: claude"):
        llm_client.get_llm_client()


def test_openai_client_requires_api_key(monkeypatch) -> None:
    from app.services.openai_client import OpenAIClient

    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required when LLM_PROVIDER is openai",
    ):
        OpenAIClient()
