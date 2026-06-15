from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

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
    ) -> StructuredResponseT:
        pass
