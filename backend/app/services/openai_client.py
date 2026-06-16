from openai import AsyncOpenAI

from app.core.config import settings
from app.services.base_llm import (
    BaseLLMClient,
    LLMStructuredResponseError,
    StructuredResponseT,
)


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

    async def generate_structured(
        self,
        prompt: str,
        *,
        response_format: type[StructuredResponseT],
    ) -> StructuredResponseT:
        response = await self.client.responses.parse(
            model=settings.OPENAI_MODEL,
            input=prompt,
            text_format=response_format,
        )

        if response.output_parsed is not None:
            return response.output_parsed

        refusal_message = None
        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                if item.type == "refusal":
                    refusal_message = item.refusal
                    break
            if refusal_message:
                break

        if refusal_message:
            raise LLMStructuredResponseError(refusal_message)

        raise LLMStructuredResponseError(
            f"failed to parse structured response as {response_format.__name__}"
        )
