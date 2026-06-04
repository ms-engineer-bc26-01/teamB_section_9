from app.core.config import settings
from app.services.base_llm import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from app.services.openai_client import OpenAIClient

        return OpenAIClient()

    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
