from openai import AsyncOpenAI

from app.core.config import settings
from app.services.base_llm import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is openai")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
        )

        return response.output_text
