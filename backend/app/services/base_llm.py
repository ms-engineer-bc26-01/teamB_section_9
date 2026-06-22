from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.services.usage import LlmUsage

StructuredResponseT = TypeVar("StructuredResponseT", bound=BaseModel)


class LLMStructuredResponseError(Exception):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        *,
        response_format: type[StructuredResponseT],
    ) -> tuple[StructuredResponseT, LlmUsage | None]:
        """構造化レスポンスと token 使用量（取得不可なら None）を返す。"""
        pass
